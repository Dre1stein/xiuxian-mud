"""装备配置加载器"""
import os
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path


class EquipmentConfigLoader:
    """装备配置加载器"""

    def __init__(self, config_dir: str = "config/equipment"):
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, Any] = {}

    def _load_yaml(self, filename: str) -> Dict:
        """加载 YAML 文件"""
        if filename in self._cache:
            return self._cache[filename]

        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"配置文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self._cache[filename] = data
            return data

    def load_rarities(self) -> Dict:
        """加载稀有度配置"""
        data = self._load_yaml("rarities.yaml")
        return data.get("rarities", {})

    def load_affixes(self) -> Dict:
        """加载词缀配置"""
        data = self._load_yaml("affixes.yaml")
        return {
            "prefixes": data.get("prefixes", []),
            "suffixes": data.get("suffixes", []),
            "legendary": data.get("legendary_affixes", []),
        }

    def load_sets(self) -> List[Dict]:
        """加载套装配置"""
        data = self._load_yaml("sets.yaml")
        return data.get("sets", [])

    def load_drop_tables(self) -> Dict:
        """加载掉落表配置"""
        data = self._load_yaml("drop_tables.yaml")
        return data.get("drop_tables", {})

    def load_exclusions(self) -> Dict:
        """加载词缀互斥规则"""
        data = self._load_yaml("affix_exclusions.yaml")
        return data.get("exclusive_groups", [])

    def get_rarity(self, rarity_name: str) -> Optional[Dict]:
        """获取单个稀有度配置"""
        rarities = self.load_rarities()
        return rarities.get(rarity_name)

    def get_affix_by_id(self, affix_id: str) -> Optional[Dict]:
        """通过ID获取词缀"""
        affixes = self.load_affixes()
        for affix_type in ["prefixes", "suffixes", "legendary"]:
            for affix in affixes.get(affix_type, []):
                if affix.get("id") == affix_id:
                    affix["category"] = affix_type
                    return affix
        return None

    def get_set_by_id(self, set_id: str) -> Optional[Dict]:
        """通过ID获取套装"""
        sets = self.load_sets()
        for s in sets:
            if s.get("set_id") == set_id:
                return s
        return None

    def get_drop_table(self, table_name: str) -> Optional[Dict]:
        """获取掉落表"""
        tables = self.load_drop_tables()
        return tables.get(table_name)

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()

    def reload_all(self):
        """重新加载所有配置"""
        self.clear_cache()
        self.load_rarities()
        self.load_affixes()
        self.load_sets()
        self.load_drop_tables()
        self.load_exclusions()


# 全局配置加载器实例
_config_loader: Optional[EquipmentConfigLoader] = None


def get_config_loader() -> EquipmentConfigLoader:
    """获取全局配置加载器"""
    global _config_loader
    if _config_loader is None:
        _config_loader = EquipmentConfigLoader()
    return _config_loader
