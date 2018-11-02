import rpyc
import hashlib
import os
import sys

"""
A client is a program that interacts with SurfStore. It is used to create,
modify, read, and delete files.  Your client will call the various file
modification/creation/deletion RPC calls.  We will be testing your service with
our own client, and your client with instrumented versions of our service.
"""

class SurfStoreClient():

	"""
	Initialize the client and set up connections to the block stores and
	metadata store using the config file
	"""
	def __init__(self, config):
		confdict = {} # config dictionary
		# file reading and parsing
		file = open(config, 'r')
		data = file.read()
		file.close()
		list_dat = data.split('\n')
		list_dat.remove('')
		for element in list_dat:
			a, b = element.split(': ')
			confdict.update({a, b})
		self.no_of_blockstores = int(confdict['B'])
		del confdict['B']
		metadata_ip_port = confdict['metadata']
		# confdict now only has the values of the blockstore
		del confdict['metadata']
		# connects to the metaDataStore server
		self.metaDataStore = rpyc.connect(metadata_ip_port.split(':')[0], metadata_ip_port.split(':')[1])
		self.fileverdict = {}

	"""
	upload(filepath) : Reads the local file, creates a set of
	hashed blocks and uploads them onto the MetadataStore
	(and potentially the BlockStore if they were not already present there).
	"""
	def upload(self, filepath):
		rpath = os.path.realpath(filepath)
		filename = rpath.split('/')[len(rpath.split('/'))-1]
		file = open(rpath, 'rb')
		# utf-8 and bytes formatting changes?
		data = file.read()
		file.close()
		# create hashlist
		hash_dict = self.hasher(data, version)
		hash_list = []
		for key, value in hash_dict.items():
			hashlist.append(key)
		# we have the hashlist!
		# initial modify (If this works, that means the filename sent is new)
		try:
			missing_hashlist, version = self.metaDataStore.modify_file(filename, 1, hashlist)
		except ErrorResponse as e:
			eprint("Some error happening!")
			print("Not Found")

	def hasher(self, data, version):
		hash_dict = {}
		from math import ceil as ceiling
		for x in range(ceiling(len(data)/4096)):
			block = data[4096*x:4096*(x+1)]
			hash = hashlib.sha1(block).hexdigest()
			hash_dict.include({hash:block})
		return hash_dict

	"""
	delete(filename) : Signals the MetadataStore to delete a file.
	"""
	def delete(self, filename):
		hashlist, version = self.metaDataStore.read_file(filename)
		if not hashlist:
			print("OK")
			pass
		else:
			try:
				if self.metaDataStore.delete_file(filename, version):
					print("OK")
			except ErrorResponse as e:
				eprint(e.argv)
				print("OK")

	"""
        download(filename, dst) : Downloads a file (f) from SurfStore and saves
        it to (dst) folder. Ensures not to download unnecessary blocks.
	"""
	def download(self, filename, location):
		pass

	"""
	 Use eprint to print debug messages to stderr
	 E.g -
	 self.eprint("This is a debug message")
	"""
	def eprint(*args, **kwargs):
		print(*args, file=sys.stderr, **kwargs)



if __name__ == '__main__':
	client = SurfStoreClient(sys.argv[1])
	operation = sys.argv[2]
	if operation == 'upload':
		client.upload(sys.argv[3])
	elif operation == 'download':
		client.download(sys.argv[3], sys.argv[4])
	elif operation == 'delete':
		client.delete(sys.argv[3])
	else:
		print("Invalid operation")
