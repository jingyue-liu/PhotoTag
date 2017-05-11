from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import json
from CREDENTIAL import Access_Key_ID, Secret_Access_Key
from sklearn.cluster import KMeans
import numpy as np

host = 'search-phototag-engmduyin6dydflby5drspxf3i.us-east-1.es.amazonaws.com'
awsauth = AWS4Auth(Access_Key_ID, Secret_Access_Key, "us-east-1" , 'es')

es = Elasticsearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)

def getClusters(clusterNum):
    res = es.search(index="cc-project", size=300)
    name_tags={}
    TAGS = set()
    for re in res['hits']['hits']:
        try:
            name_tags[re['_source']['name']]=re['_source']['tags']
            for item in re['_source']['tags']:
                TAGS.add(item)
        except Exception as e:
            pass
    TAGS = list(TAGS)
    # print TAGS
    # print name_tags
    TAGS_len = len(TAGS)
    name_vector = {}
    for key, value in name_tags.items():
        name_vector[key] = [0]*TAGS_len
        for i in value:
            name_vector[key][TAGS.index(i)] = 1
    # print name_vector

    xx = []
    xx_name = []
    for value in name_vector.items():
        xx.append(value[1])
        xx_name.append(value[0])
    X = np.array(xx)
    kmeans = KMeans(n_clusters = 10, random_state=0).fit(X)


    s3_client = boto3.client('s3',
                       aws_access_key_id=Access_Key_ID,
                       aws_secret_access_key=Secret_Access_Key,
                       region_name="us-east-1")
    cluster_name=[]
    for i in range(len(kmeans.labels_.tolist())):
        if kmeans.labels_[i] == clusterNum:
            cluster_name.append(xx_name[i])

    urls = {}
    for i in cluster_name:
        url = s3_client.generate_presigned_url(ClientMethod='get_object',
             Params={ 'Bucket': "photo-uploaded", 'Key': i})
        urls[i] = url

    return urls
