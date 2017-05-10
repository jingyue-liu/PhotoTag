from flask import Flask, jsonify, request
from flask_restful import reqparse, abort, Api, Resource
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import json
from werkzeug.datastructures import FileStorage
from cStringIO import StringIO
from CREDENTIAL import Access_Key_ID, Secret_Access_Key

import base64


## config
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png']


## app initilization
app = Flask(__name__)
app.config.from_object(__name__)

## extensions
api = Api(app)

## elastic search
host = 'search-myes-2lw4nshx535kfrodcfmvmcxqra.us-east-1.es.amazonaws.com'
awsauth = AWS4Auth(Access_Key_ID, Secret_Access_Key, "us-east-1" , 'es')

es = Elasticsearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)



## Helper Methods
def abort_if_todo_doesnt_exist(todo_id):
    if todo_id not in TODOS:
        abort(404, message="Todo {} doesn't exist".format(todo_id))

parser = reqparse.RequestParser()
parser.add_argument('task')


# Tags
class Tags(Resource):
    def get(self, tag_name):
        res = es.search(index="cc-project",
                       body={"query": {
                           'match': { 'tags': tag_name }
                          }})
        data = []
        for re in res['hits']['hits']:
            try:
                data.append(re['_source']['name'])
            except Exception as e:
                pass

        return json.loads(json.dumps({'imgs':data}))

# get a images tags
class ImgTags(Resource):
    def get(self, img_name):
        print img_name
        res = es.search(index="cc-project",
                       body={"query": {"match_phrase": {
                                "name": img_name }}})
        data = []
        print res
        for re in res['hits']['hits']:
            try:
                data = re['_source']['tags']
            except Exception as e:
                pass
        s3_client = boto3.client('s3',
                    aws_access_key_id=Access_Key_ID,
                    aws_secret_access_key=Secret_Access_Key,
                    region_name="us-east-1")
        # upload to s3
        url = s3_client.generate_presigned_url(ClientMethod='get_object',
                                    Params={ 'Bucket': "photo-uploaded", 'Key': image.filename})
        return json.loads(json.dumps({'tags':data}))


# get all kinds of tags from TagList
class TagList(Resource):
    def get(self):
        res = es.search(index="cc-project", body={"query": {"match_all": {}}})
        TAGS = set()
        for re in res['hits']['hits']:
            try:
                print re['_source']['tags']
                for item in re['_source']['tags']:
                    TAGS.add(item)
            except Exception as e:
                pass
        return json.loads(json.dumps({'tags':list(TAGS)}))


## API Endpoints
class UploadImage(Resource):
    def post(self):
        #TODO: a check on file size needs to be there.
        parse = reqparse.RequestParser()
        parse.add_argument('image', type=FileStorage, location='files')
        args = parse.parse_args()
        image = args['image']

        # check logo extension
        extension = image.filename.rsplit('.', 1)[1].lower()
        if '.' in image.filename and not extension in app.config['ALLOWED_EXTENSIONS']:
            abort(400, message="File extension is not one of our supported types.")

        # create a file object of the image
        image_file = StringIO()
        image.save(image_file)
        image_file.seek(0)

        s3 = boto3.resource('s3',
                            aws_access_key_id=Access_Key_ID,
                            aws_secret_access_key=Secret_Access_Key,
                            region_name="us-east-1")

        s3.Object("photo-uploaded" , image.filename).put(Body=image_file)

        image_file.close()
        s3_client = boto3.client('s3',
                    aws_access_key_id=Access_Key_ID,
                    aws_secret_access_key=Secret_Access_Key,
                    region_name="us-east-1")
        # upload to s3
        url = s3_client.generate_presigned_url(ClientMethod='get_object',
                                    Params={ 'Bucket': "photo-uploaded", 'Key': image.filename})
        return {'img_url': url}, 201

## Upload encode
class HelloWorld(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        filename = json_data['name']
        img_data = json_data['image']
        s3_client = boto3.client('s3',
                    aws_access_key_id=Access_Key_ID,
                    aws_secret_access_key=Secret_Access_Key,
                    region_name="us-east-1")

        # s3.Object("photo-uploaded" , filename).put(Body=base64.decodebytes(img_data))

        with open("imageToSave.png", "wb") as fh:
            fh.write(base64.decodebytes(img_data))
        s3_client.upload_file('imageToSave.png', 'photo-uploaded', filename)

        # upload to s3
        url = s3_client.generate_presigned_url(ClientMethod='get_object',
                                    Params={ 'Bucket': "photo-uploaded", 'Key': image.filename})
        return {'img_url': url}, 201

## Actually setup the Api resource routing here

api.add_resource(UploadImage, '/upload_image')
api.add_resource(TagList, '/taglist')
api.add_resource(ImgTags, '/image/<string:img_name>')
api.add_resource(Tags, '/tags/<string:tag_name>')

api.add_resource(HelloWorld, '/test')


if __name__ == '__main__':
    app.run(debug=True)