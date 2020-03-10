FROM python:3.7.6
ADD stream-to-adw.py \
logs-webserver.py /
RUN pip install --upgrade pip; \
pip install cx_Oracle; \
pip install oci; \
pip install requests 
ADD config /root/.oci/
ADD oci_api_key.pem /
CMD python3 stream-to-adw.py
