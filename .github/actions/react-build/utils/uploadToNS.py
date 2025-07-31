import os
import sys
import requests
import hmac
import hashlib
import time
import base64


# hostname = os.getenv("HOST_NAME")
# cpcode = os.getenv("CP_CODE")
# account_name = os.getenv("ACCOUNT_NAME")
# api_key = os.getenv("API_KEY").encode('utf-8')
# unique_client_id = os.getenv("UNIQUE_CLIENT_ID")
# environment = os.getenv("env")
# remote_ns_path = os.getenv("remote_path")
# remote_path = f"{environment}/{remote_ns_path}"



hostname = os.getenv("HOST_NAME")
cpcode = os.getenv("CP_CODE")
account_name = os.getenv("ACCOUNT_NAME")
api_key = os.getenv("API_KEY").encode('utf-8')
unique_client_id = os.getenv("UNIQUE_CLIENT_ID")
environment = os.getenv("environment")
remote_ns_path = os.getenv("remote_path")
remote_path = f"{environment}/{remote_ns_path}"


timestamp = str(int(time.time()))
auth_data = f"5, 0.0.0.0, 0.0.0.0, {timestamp}, {unique_client_id}, {account_name}"
action = "version=1&action=upload"


def upload_files_and_folders(directory):
    for file_name in os.listdir(directory):
        print(f"uploading file ---------> {file_name}")
        local_path = os.path.join(directory, file_name)
        ns_file_path = os.path.basename(file_name)
        path = f"/{cpcode}/{remote_path}/{ns_file_path}"
        string_to_sign = f"{auth_data}{path}\nx-akamai-acs-action:{action}\n"
        signature = hmac.new(api_key, string_to_sign.encode('utf-8'), hashlib.sha256).digest()
        base64_encoded_signature = base64.b64encode(signature).decode('utf-8')
        headers = {
            "X-Akamai-ACS-Action": action,
            "X-Akamai-ACS-Auth-Data": auth_data,
            "X-Akamai-ACS-Auth-Sign": base64_encoded_signature,
            "Host": hostname
        }
        upload_url = f"https://{hostname}{path}"
        with open(local_path, "rb") as file_data:
            #print("Headers:\n", headers)
            response = requests.put(upload_url, data=file_data, headers=headers)
            print("Status Code:", response.status_code)
            #print("Response Text:", response.text)
            #print("Response Headers:", response.headers)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("uploading files from path:  ", sys.argv[1])
        static_assets_dir = sys.argv[1].strip()
        if os.path.exists(static_assets_dir):
            upload_files_and_folders(static_assets_dir)
        else:
            print("The specified directory does not exist.")
    else:
        print("No argument provided.")