#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import argparse
import requests
from typing import List
from urllib.parse import urljoin
from pathlib import Path
from tqdm import trange

from misc import get_ignore_lst


class UploadCilent(object):
    def __init__(self, host: str, token: str, is_replace: bool = True, ignore_lst: List = []) -> None:
        self.host = host
        self.token = token
        self.force_replacing = is_replace
        self.ignore = ignore_lst
        self.ignore = self.ignore + get_ignore_lst()

    def get_upload_link(self, path: str = "/") -> str:
        response = requests.get(
            urljoin(self.host, f'/api/v2.1/via-repo-token/upload-link/?path={path}'),
            headers={'Authorization': f'Token {self.token}'}
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[Error: {response.status_code}]")
            return None
    
    def list_remote_files(self, remote_path: str,  mode: str = "f", recursive: bool = False):
        params = [f"path={remote_path}"]
        if mode == "f":
            params.append("type=f")
        elif mode == "d":
            params.append("type=d")

        if recursive:
            params.append("recursive=1")
        if params:
            pstr = "?" + "&".join(params)

        response = requests.get(
            urljoin(self.host, f"/api/v2.1/via-repo-token/dir/{pstr}") , headers={'Authorization': f'Token {self.token}'}
        )

        detailed_info = response.json()
        item_path = []
        for item in detailed_info["dirent_list"]:
            if item["parent_dir"] != "/":
                item_path.append(item["parent_dir"].lstrip("/") + "/" + item["name"])
            else:
                item_path.append(item["name"])
        return set(item_path)
    
    def get_file_lst(self, local_path: str, remote_path: str, force_replacing: bool):
        file_lst = []
        if not os.path.exists(local_path):
            print("Upload file not exists")
            return file_lst
        if os.path.isfile(local_path):
            file_lst.append(local_path)
            return file_lst
        else:
            local_files = set([f.relative_to(local_path).as_posix() for f in Path(local_path).rglob("**/*") if f.is_file()])
            file_lst = local_files
            if not force_replacing:
                remote_files = set([Path(f).relative_to(remote_path).as_posix() for f in self.list_remote_files(remote_path)])
                file_lst = local_path.difference(remote_files)
            return file_lst
    
    def _upload(self, upload_link: str, files: List, local_path: str, remote_path: str, replace: bool = False):
        print("--------------")
        cnt = 0
        files_list = list(files)
        files_list.sort()
        for file in trange(files_list):
            data = {
                'filename': Path(file).name,
                'parent_dir': remote_path,
                'replace': replace
            }
            if Path(file).parent.as_posix() != ".":
                data['relative_path'] = Path(file).parent.as_posix()
            print(f"Uploading {file}... ({cnt+1}/{len(files)})\r", end="")

            resp = requests.post(
                upload_link, data=data,
                files={'file': open(Path(local_path).joinpath(file), 'rb')},
                headers={f'Authorization': 'Token {self.token}'}
            )

            if resp.status_code == 200:
                cnt += 1
                print(f"Successfully uploaded {file} ({cnt}/{len(files)})", end="\n")
            else:
                print(f"[Error {resp.status_code}] Failed to upload {file} ({cnt}/{len(files)})", end="\n")
        print("--------------")
    
    def upload_files(self, local_path: str = "./", remote_path: str = "/", replace: bool = False) -> None:
        local_files = self.get_file_lst(local_path, remote_path, force_replacing=self.force_replacing, force_replacing=replace)
        upload_link = self.get_upload_link(path=remote_path)
        self._upload(upload_link, local_files, local_path, remote_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="Seafile server host", type=str, default="https://box.nju.edu.cn")
    parser.add_argument("token", help="API Token of Seafile repo", type=str)
    parser.add_argument("loc_dir", help="Local directory where your data is placed", type=str)
    parser.add_argument("rem_dir", help="Remote directory in Seafile repo where your data will be uploaded to", type=str)
    parser.add_argument("--relacing", help="whether to overwrite file when it already exists", type=bool, default=False)

    args = parser.parse_args()

    data_repo = UploadCilent(args.host, args.token)
    data_repo.upload_files(args.loc_dir, args.rem_dir, args.replace)
