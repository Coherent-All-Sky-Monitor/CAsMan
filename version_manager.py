#!/usr/bin/env python3
"""
CAsMan Version Manager

This script helps manage version numbers across the CAsMan project.
It updates version numbers in all relevant files and can create git tags.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union


class VersionManager:
    """Manages version numbers across the CAsMan project."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.version_files: Dict[str, Dict[str, Union[Path, str]]] = {
            "pyproject.toml": {
                "path": project_root / "pyproject.toml",
                "pattern": r'version = "([^"]+)"',
                "replacement": 'version = "{version}"',
            },
            "casman/__init__.py": {
                "path": project_root / "casman" / "__init__.py",
                "pattern": r'__version__ = "([^"]+)"',
                "replacement": '__version__ = "{version}"',
            },
            "casman/cli/utils.py": {
                "path": project_root / "casman" / "cli" / "utils.py",
                "pattern": r"from casman import __version__",
                "replacement": "from casman import __version__",
            },
        }

    def get_current_version(self) -> str:
        """Get the current version from pyproject.toml."""
        pyproject_path = self.version_files["pyproject.toml"]["path"]
        pattern = self.version_files["pyproject.toml"]["pattern"]

        try:
            content = pyproject_path.read_text(encoding="utf-8")  # type: ignore
            match = re.search(pattern, content)  # type: ignore
            if match:
                return match.group(1)
            else:
                raise ValueError("Could not find version in pyproject.toml")
        except FileNotFoundError:
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    def parse_version(self, version: str) -> tuple[int, int, int]:
        """Parse a semantic version string into components."""
        try:
            parts = version.split(".")
            if len(parts) != 3:
                raise ValueError("Version must be in format MAJOR.MINOR.PATCH")
            return int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError as e:
            raise ValueError(f"Invalid version format '{version}': {e}")

    def increment_version(self, current_version: str, change_type: str) -> str:
        """Increment version based on change type."""
        major, minor, patch = self.parse_version(current_version)

        if change_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif change_type == "minor":
            minor += 1
            patch = 0
        elif change_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid change type: {change_type}")

        return f"{major}.{minor}.{patch}"

    def validate_version(self, version: str) -> bool:
        """Validate version format."""
        try:
            self.parse_version(version)
            return True
        except ValueError:
            return False

    def update_version_in_file(self, file_key: str, new_version: str) -> bool:
        """Update version in a specific file."""
        file_info = self.version_files[file_key]
        file_path = file_info["path"]  # type: ignore
        pattern = file_info["pattern"]  # type: ignore
        replacement = file_info["replacement"]  # type: ignore

        if not file_path.exists():  # type: ignore
            print(f"⚠️  Warning: {file_path} not found, skipping")
            return False

        try:
            content = file_path.read_text(encoding="utf-8")  # type: ignore

            # Check if pattern matches
            if not re.search(pattern, content):  # type: ignore
                print(f"⚠️  Warning: Version pattern not found in {file_path}")
                return False

            # Update version
            new_content = re.sub(pattern, replacement.format(version=new_version), content)  # type: ignore

            # Write back
            file_path.write_text(new_content, encoding="utf-8")  # type: ignore
            print(f"✅ Updated {file_key}")
            return True

        except (OSError, IOError, UnicodeDecodeError) as e:
            print(f"❌ Error updating {file_path}: {e}")
            return False

    def update_all_versions(self, new_version: str) -> List[Path]:
        """Update version in all tracked files."""
        updated_files = []

        for file_key in self.version_files:
            if self.update_version_in_file(file_key, new_version):
                updated_files.append(self.version_files[file_key]["path"])  # type: ignore

        return updated_files

    def show_current_versions(self) -> None:
        """Show current versions in all files."""
        print("📋 Current versions in files:")
        print()

        for file_key, file_info in self.version_files.items():
            file_path = file_info["path"]  # type: ignore
            pattern = file_info["pattern"]  # type: ignore

            if not file_path.exists():  # type: ignore
                print(f"❌ {file_key}: File not found")
                continue

            try:
                content = file_path.read_text(encoding="utf-8")  # type: ignore
                match = re.search(pattern, content)  # type: ignore
                if match:
                    # Check if there's a capture group (version number)
                    if match.groups():
                        version = match.group(1)
                        print(f"✅ {file_key}: {version}")
                    else:
                        print(f"✅ {file_key}: Uses dynamic version import")
                else:
                    print(f"⚠️  {file_key}: Version pattern not found")
            except (OSError, IOError, UnicodeDecodeError) as e:
                print(f"❌ {file_key}: Error reading file - {e}")

    def create_git_tag(self, version: str, message: Optional[str] = None) -> bool:
        """Create a git tag for the version."""
        tag_name = f"v{version}"

        try:
            # Check if tag already exists
            result = subprocess.run(
                ["git", "tag", "-l", tag_name],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                check=False,
            )

            if result.stdout.strip():
                print(f"⚠️  Tag {tag_name} already exists")
                return False

            # Create tag
            cmd = ["git", "tag", "-a", tag_name]
            if message:
                cmd.extend(["-m", message])
            else:
                cmd.extend(["-m", f"Release version {version}"])

            result = subprocess.run(cmd, cwd=self.project_root, check=False)

            if result.returncode == 0:
                print(f"✅ Created git tag: {tag_name}")
                return True
            else:
                print("❌ Failed to create git tag")
                return False

        except (OSError, subprocess.SubprocessError) as e:
            print(f"❌ Error creating git tag: {e}")
            return False

    def commit_version_changes(
        self, new_version: str, updated_files: List[Path], message: Optional[str] = None
    ) -> bool:
        """Commit version changes to git."""
        if not updated_files:
            print("⚠️  No files to commit")
            return False

        try:
            # Add files
            for file_path in updated_files:
                subprocess.run(
                    ["git", "add", str(file_path)], cwd=self.project_root, check=False
                )

            # Commit
            commit_message = message if message else f"Bump version to {new_version}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.project_root,
                check=False,
            )

            if result.returncode == 0:
                print(f"✅ Committed version changes: {commit_message}")
                return True
            else:
                print("❌ Failed to commit changes")
                return False

        except (OSError, subprocess.SubprocessError) as e:
            print(f"❌ Error committing changes: {e}")
            return False


def get_change_type_interactive() -> str:
    """Get change type from user interactively."""
    print("\n🔄 What type of change are you making?")
    print()
    print("1. 🚀 Major (breaking changes, new major features)")
    print("   Example: 1.2.3 → 2.0.0")
    print()
    print("2. ✨ Minor (new features, backward compatible)")
    print("   Example: 1.2.3 → 1.3.0")
    print()
    print("3. 🐛 Patch (bug fixes, small improvements)")
    print("   Example: 1.2.3 → 1.2.4")
    print()

    while True:
        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == "1":
            return "major"
        elif choice == "2":
            return "minor"
        elif choice == "3":
            return "patch"
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="CAsMan Version Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --show                     # Show current versions
  %(prog)s --increment patch          # Increment patch version
  %(prog)s --set 1.2.3               # Set specific version
  %(prog)s --increment minor --tag    # Increment minor version and create git tag
  %(prog)s --increment major --commit --tag  # Full release workflow
        """,
    )

    parser.add_argument(
        "--show", action="store_true", help="Show current versions in all files"
    )

    parser.add_argument(
        "--increment",
        choices=["major", "minor", "patch"],
        help="Increment version by type",
    )

    parser.add_argument(
        "--set", metavar="VERSION", help="Set specific version (e.g., 1.2.3)"
    )

    parser.add_argument(
        "--commit", action="store_true", help="Commit version changes to git"
    )

    parser.add_argument(
        "--commit-message", metavar="MESSAGE", help="Custom message for git commit"
    )

    parser.add_argument(
        "--tag", action="store_true", help="Create git tag for the version"
    )

    parser.add_argument(
        "--tag-message", metavar="MESSAGE", help="Custom message for git tag"
    )

    args = parser.parse_args()

    # Find project root
    project_root = Path(__file__).parent
    if not (project_root / "pyproject.toml").exists():
        print(
            "❌ Error: pyproject.toml not found. Make sure you're running this from the project root."
        )
        sys.exit(1)

    vm = VersionManager(project_root)

    # Show current versions
    if args.show:
        vm.show_current_versions()
        return

    # If no action specified, run interactive mode
    if not args.increment and not args.set:
        print("🎯 CAsMan Version Manager")
        print("=" * 40)

        vm.show_current_versions()

        change_type = get_change_type_interactive()
        current_version = vm.get_current_version()
        new_version = vm.increment_version(current_version, change_type)

        print(f"\n📈 Version change: {current_version} → {new_version}")

        confirm = input("\nProceed with this version update? (y/N): ").strip().lower()
        if confirm != "y":
            print("❌ Version update cancelled")
            sys.exit(0)

        # Ask about git operations
        commit = input("Commit changes to git? (y/N): ").strip().lower() == "y"
        commit_message = None
        if commit:
            commit_message = input("Commit message (optional): ").strip() or None
        tag = input("Create git tag? (y/N): ").strip().lower() == "y"
        tag_message = None
        if tag:
            tag_message = input("Tag message (optional): ").strip() or None

    else:
        # Command line mode
        current_version = vm.get_current_version()

        if args.increment:
            new_version = vm.increment_version(current_version, args.increment)
        elif args.set:
            if not vm.validate_version(args.set):
                print(f"❌ Invalid version format: {args.set}")
                sys.exit(1)
            new_version = args.set

        commit = args.commit
        commit_message = args.commit_message
        tag = args.tag
        tag_message = args.tag_message

        print(f"📈 Version change: {current_version} → {new_version}")

    # Update versions
    print(f"\n🔄 Updating version to {new_version}...")
    updated_files = vm.update_all_versions(new_version)

    if not updated_files:
        print("❌ No files were updated")
        sys.exit(1)

    print(f"\n✅ Successfully updated {len(updated_files)} files")

    # Git operations
    if commit:
        print("\n📝 Committing changes...")
        vm.commit_version_changes(new_version, updated_files, commit_message)

    if tag:
        print("\n🏷️  Creating git tag...")
        vm.create_git_tag(new_version, tag_message)

    print(f"\n🎉 Version update complete: {new_version}")

    if commit or tag:
        print("\n💡 Next steps:")
        if commit:
            print("   git push origin <branch>  # Push commits")
        if tag:
            print("   git push origin --tags    # Push tags")


if __name__ == "__main__":
    main()
