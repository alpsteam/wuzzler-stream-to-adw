# Stream to ADW

Create `config` file with 
```
[OCI_CLI_SETTINGS]
default_profile=DEFAULT
[DEFAULT]
user=ocid1.user.oc1..xxxxx
fingerprint=xxxxx
key_file=/oci_api_key.pem
tenancy=ocid1.tenancy.oc1..xxxxx
region=xxxxx
pass_phrase=xxxxx
```
and include `/oci_api_key.pem` file.
```
docker build -t stream-to-adw . 
docker run -it stream-to-adw:latest
```

`docker tag` and `docker push`