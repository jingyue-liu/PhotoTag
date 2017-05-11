from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import json
from CREDENTIAL import Access_Key_ID, Secret_Access_Key
from sklearn.cluster import KMeans
import numpy as np

host = 'search-myes-2lw4nshx535kfrodcfmvmcxqra.us-east-1.es.amazonaws.com'
awsauth = AWS4Auth(Access_Key_ID, Secret_Access_Key, "us-east-1" , 'es')

es = Elasticsearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)


res = es.search(index="cc-project", size=300)
name_tags={}
TAGS = set()
for re in res['hits']['hits']:
    try:
        #print re['_source']
        name_tags[re['_source']['name']]=re['_source']['tags']
        for item in re['_source']['tags']:
            TAGS.add(item)        
    except Exception as e:
        pass
#print json.loads(json.dumps({'tags':list(TAGS)}))
TAGS = list(TAGS)
print TAGS
#print name_tags
TAGS_len = len(TAGS)
name_vector = {}    
for key, value in name_tags.items():
    name_vector[key] = [0]*TAGS_len
    for i in value:
        name_vector[key][TAGS.index(i)] = 1
#print name_vector

xx = []
xx_name = []
#for i in name_vector:
#    print i
#    xx.append[i[1]]
for value in name_vector.items():
    #print value[1]
    xx.append(value[1])
    xx_name.append(value[0])
print xx_name    
X = np.array(xx)
kmeans = KMeans(n_clusters = 10, random_state=0).fit(X)
print kmeans.labels_
print kmeans.cluster_centers_

s3_client = boto3.client('s3',
                   aws_access_key_id=Access_Key_ID,
                   aws_secret_access_key=Secret_Access_Key,
                   region_name="us-east-1")
cluster_name=[]
for i in range(len(kmeans.labels_.tolist())):
    if kmeans.labels_[i] == 9:
        print xx_name[i]
        cluster_name.append(xx_name[i])
        print i
        
for i in cluster_name:
    url = s3_client.generate_presigned_url(ClientMethod='get_object',
         Params={ 'Bucket': "photo-uploaded", 'Key': i})
    print url
