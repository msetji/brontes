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

#secret_properties = client.list_properties_of_secrets()
secret_properties = list(client.list_properties_of_secrets())
properties = [prop for prop in secret_properties if not prop.name.endswith("LIVE") and not prop.name.endswith("DEV") and prop._attributes.enabled]

live_properties = [prop for prop in secret_properties if prop.name.endswith("LIVE") and prop._attributes.enabled]

dev_properties = [prop for prop in secret_properties if prop.name.endswith("DEV") and prop._attributes.enabled]

secrets = {}
for secret in properties:
    secret_name = secret.name
    secret_value = client.get_secret(secret_name).value
    secrets[secret_name] = client.get_secret(secret_name).value

live_secrets = {}
for secret in live_properties:
    secret_name = secret.name
    secret_value = client.get_secret(secret_name).value
    live_secrets[secret_name] = client.get_secret(secret_name).value

dev_secrets = {}
for secret in dev_properties:
    secret_name = secret.name
    secret_value = client.get_secret(secret_name).value
    dev_secrets[secret_name] = client.get_secret(secret_name).value

with open(".env.staging", "w") as env_file:
    for secret_name, secret_value in secrets.items():
        env_file.write(f'{secret_name.upper().replace("-","_")}="{secret_value}"\n')

with open(".env.prod", "w") as env_file:
    for secret_name, secret_value in live_secrets.items():
        env_file.write(f'{secret_name.upper().replace("-LIVE","").replace("-","_")}="{secret_value}"\n')

with open(".env", "w") as env_file:
    for secret_name, secret_value in dev_secrets.items():
        env_file.write(f'{secret_name.upper().replace("-DEV","").replace("-","_")}="{secret_value}"\n')
