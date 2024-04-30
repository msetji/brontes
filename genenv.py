# run this code to populate the key values to the staging env file (you need to have the correct permissions to access the key vault)
# Steps:
# 1. az login
# 2. python3 genenv.py   

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

kv_name = "OpenOperatorKeyVault"
kv_url = f"https://openoperatorkeyvault.vault.azure.net/"

cred = DefaultAzureCredential()

client = SecretClient(vault_url=kv_url,credential=cred)

secret_properties = client.list_properties_of_secrets()

secrets = {}
for secret in secret_properties:
    secret_name = secret.name
    secret_value = client.get_secret(secret_name).value
    secrets[secret_name] = client.get_secret(secret_name).value

with open(".env.staging", "w") as env_file:
    for secret_name, secret_value in secrets.items():
        env_file.write(f'{secret_name.upper().replace("-","_")}="{secret_value}"\n')
