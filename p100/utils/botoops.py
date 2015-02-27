REGION = 'us-west-2'
BUCKET = 'p100-analytics'
TEMP = '/scratch/'

import os, hashlib, sys
import boto.kms
import boto
from boto.s3.key import Key
import json

class BotoOps:

    def get_credentials(self, credentials_file, bucket=BUCKET, region=REGION ):
        """
        This method hit the s3 bucket and pulls down the credentials
        file which is encrypted by a kms key that this iam role has
        decrypt privileges to.
        """

        s3 = boto.connect_s3()
        b = s3.get_bucket(bucket)
        k = Key(b)
        k.key = credentials_file
        kms = boto.kms.connect_to_region(region)
        return json.loads(kms.decrypt(k.get_contents_as_string())['Plaintext'])

    def compare_checksum(self, path, prefix, bucket, region=REGION):

        s3 = boto.connect_s3()
        b = s3.get_bucket(bucket)
        key = b.get_key(prefix)
        remote_digest = key.etag[1 :-1]
        print digest

    def copy_s3_to_ephemeral(self, prefix, bucket, region=REGION):

        filename = os.path.basename(prefix)
        new_filename = TEMP+filename

        s3 = boto.connect_s3()
        b = s3.get_bucket(bucket)
        k = b.get_key(prefix)
        k.get_contents_to_filename(new_filename)
        print "Downloaded %s from bucket %s"%(filename, bucket)
        return new_filename

    def percent_cb(self, complete, total):
        sys.stdout.write("Uploaded %.2f percent\n"%((float(complete) / float(total))*100.0))
        sys.stdout.flush()

    def copy_ephemeral_to_s3(self, filename, bucket, path='', region=REGION):

        # Get path of bucket
        s3 = boto.connect_s3()
        b = s3.get_bucket(bucket)
        k = Key(b)

        if (len(path)==0):
            k.key = filename;
        else:
            k.key = path.strip('/') + '/' + filename

        # Actually upload the file
        k.set_contents_from_filename(TEMP+filename, cb=self.percent_cb, num_cb=10)

