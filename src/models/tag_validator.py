import re
from datetime import datetime


class TagValidator:
    """Tag验证器和版本管理工具"""

    @staticmethod
    def validate_tag_name(tag_name):
        """
        验证tag名称格式

        Args:
            tag_name: 要验证的tag名称

        Returns:
            dict: {
                'valid': bool,
                'errors': list[str],
                'warnings': list[str]
            }
        """
        if not tag_name:
            return {"valid": False, "errors": ["Tag名称不能为空"], "warnings": []}

        errors = []
        warnings = []

        # Git tag命名规则
        if re.search(r"[\s~^:?*\[\]\\]", tag_name):
            errors.append("不能包含空格、~^:?*[]\\等特殊字符")

        if tag_name.startswith("."):
            errors.append("不能以.开头")

        if ".." in tag_name:
            errors.append("不能包含连续的..")

        if tag_name.endswith("."):
            errors.append("不能以.结尾")

        # 版本号格式检查
        version_match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", tag_name)
        if version_match:
            try:
                major, minor, patch = map(int, version_match.groups())

                # 检查版本号合理性
                if major < 0 or minor < 0 or patch < 0:
                    warnings.append("版本号包含负数")

                # 检查大版本号是否合理
                if major > 999:
                    warnings.append("主版本号异常大（>999），请确认是否正确")

            except ValueError:
                warnings.append("版本号格式可能不正确")

        # 检查tag名称长度
        if len(tag_name) > 100:
            warnings.append("Tag名称过长，建议控制在100字符以内")

        # 检查是否包含特殊前缀
        common_prefixes = ["v", "ver", "version", "release-", "r"]
        has_common_prefix = any(
            tag_name.lower().startswith(prefix) for prefix in common_prefixes
        )
        if not has_common_prefix and version_match:
            warnings.append("建议使用v前缀（如v1.0.0）以符合语义化版本规范")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    @staticmethod
    def parse_version(tag_name):
        """
        解析tag名称中的版本号

        Args:
            tag_name: tag名称

        Returns:
            dict or None: {
                'major': int,
                'minor': int,
                'patch': int,
                'prerelease': str or None,
                'build': str or None,
                'prefix': str
            }
        """
        # 匹配语义化版本号（SemVer）
        # 格式：v1.2.3 或 1.2.3
        # 可选预发布版本：v1.2.3-alpha.1
        # 可选构建信息：v1.2.3-alpha.1+build.123

        pattern = r"^(?P<prefix>v?)(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<prerelease>[0-9A-Za-z.-]+))?(?:\+(?P<build>[0-9A-Za-z.-]+))?$"
        match = re.match(pattern, tag_name)

        if match:
            return {
                "major": int(match.group("major")),
                "minor": int(match.group("minor")),
                "patch": int(match.group("patch")),
                "prerelease": match.group("prerelease"),
                "build": match.group("build"),
                "prefix": match.group("prefix"),
            }

        return None

    @staticmethod
    def suggest_next_version(current_version, increment_type="patch"):
        """
        根据当前版本号建议下一个版本号

        Args:
            current_version: 当前版本号（如'v1.2.3'）
            increment_type: 递增类型
                - 'patch': 补丁版本（v1.2.3 → v1.2.4）
                - 'minor': 次版本（v1.2.3 → v1.3.0）
                - 'major': 主版本（v1.2.3 → v2.0.0）
                - 'prerelease': 预发布版本（v1.2.3 → v1.2.4-alpha.1）

        Returns:
            list[str]: 建议的版本号列表
        """
        parsed = TagValidator.parse_version(current_version)
        if not parsed:
            # 如果无法解析，返回默认建议
            return ["v1.0.0"]

        suggestions = []

        major = parsed["major"]
        minor = parsed["minor"]
        patch = parsed["patch"]
        prefix = parsed["prefix"]
        prerelease = parsed.get("prerelease")

        # 根据递增类型生成建议
        if increment_type == "patch":
            # 补丁版本递增
            suggestions.append(f"{prefix}{major}.{minor}.{patch + 1}")
            # 也提供次版本和主版本建议
            suggestions.append(f"{prefix}{major}.{minor + 1}.0")
            suggestions.append(f"{prefix}{major + 1}.0.0")

        elif increment_type == "minor":
            # 次版本递增
            suggestions.append(f"{prefix}{major}.{minor + 1}.0")
            # 也提供补丁版本和主版本建议
            suggestions.append(f"{prefix}{major}.{minor}.{patch + 1}")
            suggestions.append(f"{prefix}{major + 1}.0.0")

        elif increment_type == "major":
            # 主版本递增
            suggestions.append(f"{prefix}{major + 1}.0.0")
            # 也提供次版本和补丁版本建议
            suggestions.append(f"{prefix}{major}.{minor + 1}.0")
            suggestions.append(f"{prefix}{major}.{minor}.{patch + 1}")

        elif increment_type == "prerelease":
            # 预发布版本
            if prerelease:
                # 如果已有预发布版本，递增预发布版本号
                prerelease_match = re.match(r"^(.+)\.(\d+)$", prerelease)
                if prerelease_match:
                    prerelease_type = prerelease_match.group(1)
                    prerelease_num = int(prerelease_match.group(2)) + 1
                    suggestions.append(
                        f"{prefix}{major}.{minor}.{patch}-{prerelease_type}.{prerelease_num}"
                    )
                else:
                    # 无法解析预发布版本号，添加.1
                    suggestions.append(
                        f"{prefix}{major}.{minor}.{patch}-{prerelease}.1"
                    )
            else:
                # 创建新的预发布版本
                suggestions.append(f"{prefix}{major}.{minor}.{patch + 1}-alpha.1")
                suggestions.append(f"{prefix}{major}.{minor}.{patch + 1}-beta.1")
                suggestions.append(f"{prefix}{major}.{minor}.{patch + 1}-rc.1")

        # 去重并返回前5个建议
        return list(dict.fromkeys(suggestions))[:5]

    @staticmethod
    def compare_versions(version1, version2):
        """
        比较两个版本号

        Args:
            version1: 版本号1
            version2: 版本号2

        Returns:
            int: -1 (version1 < version2), 0 (相等), 1 (version1 > version2)
        """
        v1 = TagValidator.parse_version(version1)
        v2 = TagValidator.parse_version(version2)

        if not v1 or not v2:
            return 0

        # 比较主版本
        if v1["major"] != v2["major"]:
            return -1 if v1["major"] < v2["major"] else 1

        # 比较次版本
        if v1["minor"] != v2["minor"]:
            return -1 if v1["minor"] < v2["minor"] else 1

        # 比较补丁版本
        if v1["patch"] != v2["patch"]:
            return -1 if v1["patch"] < v2["patch"] else 1

        # 如果主次补丁版本都相同，比较预发布版本
        prerelease1 = v1.get("prerelease")
        prerelease2 = v2.get("prerelease")

        if not prerelease1 and not prerelease2:
            # 都没有预发布版本，版本相同
            return 0
        elif not prerelease1:
            # v1是正式版本，v2是预发布版本
            return 1
        elif not prerelease2:
            # v2是正式版本，v1是预发布版本
            return -1
        else:
            # 都有预发布版本，按字母顺序比较
            prerelease_order = ["alpha", "beta", "rc"]

            # 尝试提取预发布类型和编号
            def parse_prerelease(prerelease):
                parts = prerelease.split(".")
                if len(parts) >= 1:
                    prerelease_type = parts[0]
                    prerelease_num = 0
                    if len(parts) >= 2:
                        try:
                            prerelease_num = int(parts[1])
                        except ValueError:
                            pass
                    return prerelease_type, prerelease_num
                return "", 0

            type1, num1 = parse_prerelease(prerelease1)
            type2, num2 = parse_prerelease(prerelease2)

            # 按预发布类型排序
            try:
                index1 = prerelease_order.index(type1)
                index2 = prerelease_order.index(type2)
                if index1 != index2:
                    return -1 if index1 < index2 else 1
            except ValueError:
                # 未知的预发布类型，按字母顺序比较
                if type1 != type2:
                    return -1 if type1 < type2 else 1

            # 比较预发布版本号
            if num1 != num2:
                return -1 if num1 < num2 else 1

            return 0

        # 比较主版本
        if v1["major"] != v2["major"]:
            return -1 if v1["major"] < v2["major"] else 1

        # 比较次版本
        if v1["minor"] != v2["minor"]:
            return -1 if v1["minor"] < v2["minor"] else 1

        # 比较补丁版本
        if v1["patch"] != v2["patch"]:
            return -1 if v1["patch"] < v2["patch"] else 1

        # 如果主次补丁版本都相同，比较预发布版本
        if v1.get("prerelease") and v2.get("prerelease"):
            # 都有预发布版本
            return 0
        elif v1.get("prerelease"):
            # v1是预发布版本，v2是正式版本
            return -1
        elif v2.get("prerelease"):
            # v2是预发布版本，v1是正式版本
            return 1
        else:
            # 都没有预发布版本
            return 0

    @staticmethod
    def format_version(version_dict, include_prefix=True):
        """
        将版本字典格式化为字符串

        Args:
            version_dict: parse_version返回的字典
            include_prefix: 是否包含前缀（如'v'）

        Returns:
            str: 格式化后的版本号
        """
        prefix = version_dict.get("prefix", "v") if include_prefix else ""
        major = version_dict["major"]
        minor = version_dict["minor"]
        patch = version_dict["patch"]
        prerelease = version_dict.get("prerelease")
        build = version_dict.get("build")

        version_str = f"{prefix}{major}.{minor}.{patch}"

        if prerelease:
            version_str += f"-{prerelease}"

        if build:
            version_str += f"+{build}"

        return version_str
