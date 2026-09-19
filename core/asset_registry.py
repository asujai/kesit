import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

REGISTRY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "asset_registry.json")

class AssetRegistry:
    def __init__(self, registry_path=REGISTRY_PATH):
        self.registry_path = registry_path
        self.data = {"assets": {}, "rejections": []}
        self.load()

    def load(self):
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8-sig") as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"[AssetRegistry] Warning loading registry: {e}. Starting fresh.")
                self.data = {"assets": {}, "rejections": []}
        else:
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        tmp_path = self.registry_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        if os.path.exists(tmp_path):
            os.replace(tmp_path, self.registry_path)

    def _key(self, provider, asset_id):
        return f"{provider}_{asset_id}"

    @classmethod
    def compute_file_hash(cls, file_path: str) -> str:
        if not file_path or not os.path.exists(file_path):
            return ""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def find_asset_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        if not file_hash:
            return None
        for k, v in self.data["assets"].items():
            if v.get("file_hash") == file_hash:
                return v
        return None

    def register_asset(self, provider: str, asset_id: str, media_type: str,
                       description: str, query: str, tags: List[str] = None,
                       file_path: Optional[str] = None) -> Dict[str, Any]:
        key = self._key(provider, asset_id)
        fhash = self.compute_file_hash(file_path) if file_path else ""

        if key not in self.data["assets"]:
            self.data["assets"][key] = {
                "provider": provider,
                "asset_id": str(asset_id),
                "media_type": media_type,
                "description": description,
                "query": query,
                "tags": tags or [],
                "file_hash": fhash,
                "created_at": datetime.now().isoformat(),
                "used_in": [],
                "status": "approved"
            }
        else:
            entry = self.data["assets"][key]
            if fhash and not entry.get("file_hash"):
                entry["file_hash"] = fhash
            if description and not entry.get("description"):
                entry["description"] = description
            if tags:
                entry["tags"] = list(set(entry.get("tags", []) + tags))

        self.save()
        return self.data["assets"][key]

    def record_usage(self, provider: str, asset_id: str, day: str, start_t: float, end_t: float, notes: str = "", file_path: str = None):
        key = self._key(provider, asset_id)
        if key not in self.data["assets"]:
            self.register_asset(provider, asset_id, "video", notes or "Auto-registered", "", file_path=file_path)

        entry = self.data["assets"][key]
        if file_path and not entry.get("file_hash"):
            entry["file_hash"] = self.compute_file_hash(file_path)

        entry.setdefault("used_in", []).append({
            "day": day,
            "start_t": round(float(start_t), 2),
            "end_t": round(float(end_t), 2),
            "duration": round(float(end_t) - float(start_t), 2),
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        })
        self.save()

    def record_rejection(self, provider: str, asset_id: str, query: str, reason: str):
        self.data.setdefault("rejections", []).append({
            "provider": provider,
            "asset_id": str(asset_id),
            "query": query,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        key = self._key(provider, asset_id)
        if key in self.data["assets"]:
            self.data["assets"][key]["status"] = "rejected"
            self.data["assets"][key]["rejection_reason"] = reason
        self.save()

    def is_rejected(self, provider: str, asset_id: str) -> bool:
        key = self._key(provider, asset_id)
        if key in self.data.get("assets", {}):
            return self.data["assets"][key].get("status") == "rejected"
        return any(r.get("provider") == provider and str(r.get("asset_id")) == str(asset_id) for r in self.data.get("rejections", []))

    def is_used_in_day(self, provider: str, asset_id: str, day: str) -> bool:
        key = self._key(provider, asset_id)
        if key not in self.data["assets"]:
            return False
        return any(u.get("day") == day for u in self.data["assets"][key].get("used_in", []))

    def get_recent_usage_days(self, provider: str, asset_id: str) -> List[str]:
        key = self._key(provider, asset_id)
        if key not in self.data["assets"]:
            return []
        return [u.get("day") for u in self.data["assets"][key].get("used_in", [])]

    def record_build_usage(self, spec: Any, build_id: str):
        """Automatically called by QualityGate upon release approval."""
        day = spec.meta.get("day", "UnknownDay")
        for cut in spec.cuts:
            if cut.get("fallback") == "speaker_cut" or not cut.get("source_file"):
                continue

            cid = cut.get("id", "")
            src_file = cut.get("source_file", "")
            st = cut.get("start_t", 0.0)
            et = cut.get("end_t", 0.0)
            
            # Resolve actual provider & asset_id via file content hash or metadata
            fhash = self.compute_file_hash(src_file) if src_file and os.path.exists(src_file) else ""
            existing_match = self.find_asset_by_hash(fhash) if fhash else None

            if existing_match:
                provider = existing_match.get("provider", "pexels")
                aid = str(existing_match.get("asset_id"))
            elif cut.get("asset_id"):
                provider = cut.get("provider", "pexels")
                aid = str(cut.get("asset_id"))
            else:
                # If neither hash nor asset_id known, try parsing provider_id from filename
                base_name = os.path.basename(src_file)
                parts = base_name.replace(".mp4", "").replace(".jpg", "").split("_")
                if len(parts) >= 3 and parts[1] in ("pexels", "pixabay", "giphy"):
                    provider = parts[1]
                    aid = parts[2]
                else:
                    provider = cut.get("provider", "local")
                    aid = cid

            self.record_usage(provider, aid, day, st, et, notes=f"Build: {build_id} (cut {cid})", file_path=src_file)

# Global singleton
registry = AssetRegistry()
