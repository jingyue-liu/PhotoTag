from __future__ import print_function

import boto3
from decimal import Decimal
import json
import urllib
from elasticsearch import Elasticsearch, RequestsHttpConnection 

print('Loading function')

rekognition = boto3.client('rekognition')


# --------------- Helper Functions to call Rekognition APIs ------------------


def detect_faces(bucket, key):
    response = rekognition.detect_faces(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    return response


def detect_labels(bucket, key):
    response = rekognition.detect_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}}, MinConfidence=90)
    return response


def index_faces(bucket, key):
    # Note: Collection has to be created upfront. Use CreateCollection API to create a collecion.
    #rekognition.create_collection(CollectionId='BLUEPRINT_COLLECTION')
    response = rekognition.index_faces(Image={"S3Object": {"Bucket": bucket, "Name": key}}, CollectionId="BLUEPRINT_COLLECTION")
    return response


#---------------- Elasticsearch ----------------

def connectES(esEndPoint):
    print('Connecting to the ES Endpoint {0}'.format(esEndPoint))
    try:
        esClient = Elasticsearch(
        hosts=[{'host': esEndPoint, 'port': 443}],
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection)
        return esClient
    except Exception as E:
        print("Unable to connect to {0}".format(esEndPoint))
        print(E)
        exit(0)

def esElement(esClient, key, response):
    try:
        tags=[]
        for i in response['Labels']:
            tags.append(i['Name'])
        tag = tags
        retval = esClient.index(index='cc-project', doc_type='images', body={
            'name': key,
            'tags': tag
        })
        return retval
    except Exception as E:
        print("Error: ",E)
        exit(0)

# --------------- Main handler ------------------


def lambda_handler(event, context):
    '''Demonstrates S3 trigger that uses
    Rekognition APIs to detect faces, labels and index faces in S3 Object.
    '''
    #print("Received event: " + json.dumps(event, indent=2))
    
    esClient = connectES('search-phototag-engmduyin6dydflby5drspxf3i.us-east-1.es.amazonaws.com')
    # Get the object from the event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.unquote_plus(record['s3']['object']['key'].encode('utf8'))
        try:
            # Calls rekognition DetectFaces API to detect faces in S3 object
            #response1 = detect_faces(bucket, key)

            # Calls rekognition DetectLabels API to detect labels in S3 object
            response = detect_labels(bucket, key)

            # Calls rekognition IndexFaces API to detect faces in S3 object and index faces into specified collection
            #response = index_faces(bucket, key)

            # Print response to console.
            print(response)
            #print(response1)
            esElement(esClient,key,response)

            return response
        except Exception as e:
            print(e)
            print("Error processing object {} from bucket {}. ".format(key, bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
            raise e
