"""CLI sub-commands for profile management, wired into the main parser."""

from __future__ import annotations

import argparse
import sys

from envault.profile import (
    add_profile,
    get_profile,
    list_profiles,
    remove_profile,
    ProfileError,
)


def cmd_profile_add(args: argparse.Namespace) -> int:
    add_profile(
        name=args.name,
        env_file=args.env_file,
        store_dir=args.store_dir,
        remote=args.remote,
    )
    print(f"Profile '{args.name}' saved.")
    return 0


def cmd_profile_show(args: argparse.Namespace) -> int:
    try:
        profile = get_profile(args.name)
    except ProfileError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"env_file : {profile['env_file']}")
    print(f"store_dir: {profile['store_dir']}")
    print(f"remote   : {profile['remote'] or '(none)'}")
    return 0


def cmd_profile_remove(args: argparse.Namespace) -> int:
    try:
        remove_profile(args.name)
    except ProfileError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Profile '{args.name}' removed.")
    return 0


def cmd_profile_list(_args: argparse.Namespace) -> int:
    names = list_profiles()
    if not names:
        print("No profiles configured.")
    else:
        for name in names:
            print(name)
    return 0


def register_profile_subparser(subparsers) -> None:
    """Attach 'profile' sub-command tree to an existing subparsers action."""
    p_profile = subparsers.add_parser("profile", help="Manage named profiles")
    ps = p_profile.add_subparsers(dest="profile_cmd", required=True)

    # add
    p_add = ps.add_parser("add", help="Add or update a profile")
    p_add.add_argument("name")
    p_add.add_argument("--env-file", required=True, dest="env_file")
    p_add.add_argument("--store-dir", required=True, dest="store_dir")
    p_add.add_argument("--remote", default=None)
    p_add.set_defaults(func=cmd_profile_add)

    # show
    p_show = ps.add_parser("show", help="Show a profile")
    p_show.add_argument("name")
    p_show.set_defaults(func=cmd_profile_show)

    # remove
    p_rm = ps.add_parser("remove", help="Remove a profile")
    p_rm.add_argument("name")
    p_rm.set_defaults(func=cmd_profile_remove)

    # list
    p_list = ps.add_parser("list", help="List all profiles")
    p_list.set_defaults(func=cmd_profile_list)
