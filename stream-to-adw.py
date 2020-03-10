#!/usr/bin/python3

import oci
import time
import argparse
import os.path
import cx_Oracle
from base64 import b64encode, b64decode
import requests 
import json
import logging
from subprocess import Popen

# set up logging
logger = logging.getLogger("file")
logger.setLevel(logging.INFO) # process everything, even if everything isn't printed
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO) # or any other level
logger.addHandler(ch)

fh = logging.FileHandler('stream-to-adw.log')
fh.setLevel(logging.INFO) # or any level you want
logger.addHandler(fh)

# set up parser
parser = argparse.ArgumentParser(description="Read OCI Stream and send to custom ADWH REST API..")
parser.add_argument("-c", "--compartment", type=str, help="OCI compartment OCID", default="ocid1.compartment.oc1..aaaaaaaadiw65ysvdvpcgfeijvcne7uadbfbnnrqyg7j4vaaadmeh6setz2a")
parser.add_argument("-s", "--stream_oci", type=str,help="OCI stream name", default="acw-stream")
parser.add_argument("-b", "--buffer_size", type=int, help="Size of write buffer", default=25)

args = parser.parse_args()

oci_stream = args.stream_oci
oci_compartment = args.compartment
adb_buffer_size = args.buffer_size
logger.info(oci_stream)
logger.info(oci_compartment)

# set up OCI streaming 

api_endpoint = "https://js7elhijapblzqx-wuzzlerdb.adb.eu-frankfurt-1.oraclecloudapps.com/ords/acw/game/"
game_id="333"

def initOCIStream():
    config = oci.config.from_file(profile_name="DEFAULT")
    # Create a StreamAdminClientCompositeOperations for composite operations.
    stream_admin_client = oci.streaming.StreamAdminClient(config)
    stream_admin_client_composite = oci.streaming.StreamAdminClientCompositeOperations(stream_admin_client)
    stream = get_or_create_stream(stream_admin_client, oci_compartment, oci_stream, 1, stream_admin_client_composite).data
    stream_client = oci.streaming.StreamClient(config, service_endpoint=stream.messages_endpoint)
    s_id = stream.id

    return stream_client, s_id

def get_or_create_stream(client, compartment_id, stream_name, partition, sac_composite):

    list_streams = client.list_streams(compartment_id=compartment_id, name=stream_name, lifecycle_state=oci.streaming.models.StreamSummary.LIFECYCLE_STATE_ACTIVE)
    if list_streams.data:
        # If we find an active stream with the correct name, we'll use it.
        logger.info("An active stream {} has been found".format(stream_name))
        sid = list_streams.data[0].id
        return get_stream(sac_composite.client, sid)

    logger.info(" No Active stream  {} has been found; Creating it now. ".format(stream_name))
    logger.info(" Creating stream {} with {} partitions.".format(stream_name, partition))

    # Create stream_details object that need to be passed while creating stream.
    stream_details = oci.streaming.models.CreateStreamDetails(name=stream_name, partitions=partition,
                                                              compartment_id=oci_compartment, retention_in_hours=24)

    # Since stream creation is asynchronous; we need to wait for the stream to become active.
    response = sac_composite.create_stream_and_wait_for_state(
        stream_details, wait_for_states=[oci.streaming.models.StreamSummary.LIFECYCLE_STATE_ACTIVE])
    return response


def get_stream(admin_client, stream_id):
    return admin_client.get_stream(stream_id)

def get_cursor_by_partition(client, stream_id, partition):
    logger.info("Creating a cursor for partition {}".format(partition))
    cursor_details = oci.streaming.models.CreateCursorDetails(
        partition=partition,
        type=oci.streaming.models.CreateCursorDetails.TYPE_LATEST)
    response = client.create_cursor(stream_id, cursor_details)
    cursor = response.data.value
    return cursor

def message_writer_loop(client, stream_id, initial_cursor):
    cursor = initial_cursor
    while True:
        get_response = client.get_messages(stream_id, cursor, limit=adb_buffer_size)
        messages = []

        # Process the messages
        # logger.info(" Read {} messages".format(len(get_response.data)))
        for message in get_response.data:
            try: 
                # logger.info("{}: {}".format(b64decode(message.key.encode()).decode(),b64decode(message.value.encode()).decode()))
                json_obj = b64decode(message.value.encode()).decode()
                # logger.info(tempi)
                messages.append(json.loads(json_obj))
            except: 
                pass

        time.sleep(3)
        if len(messages) > 0:
            payload = json.dumps(messages)
            logger.info('Got messages: ')
            logger.info(payload)
            r_v = requests.post(url = api_endpoint + "vector/" + game_id, data = payload)
            logger.info(r_v.status_code)
            # logger.info(r_v.text)

        # use the next-cursor for iteration
        cursor = get_response.headers["opc-next-cursor"]

# start the program 
p = Popen(['python3', 'logs-webserver.py']) # something long running

stream_client, stream_id = initOCIStream()
partition_cursor = get_cursor_by_partition(stream_client, stream_id, partition="0")
message_writer_loop(stream_client, stream_id, partition_cursor)
