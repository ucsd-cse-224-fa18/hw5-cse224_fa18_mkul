import rpyc
import hashlib
import os
import sys
from metastore import ErrorResponse
import json
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
			confdict.update({a: b})
		self.no_of_blockstores = int(confdict['B'])
		del confdict['B']
		metadata_ip_port = confdict['metadata']
		# confdict now only has the values of the blockstore
		del confdict['metadata']
		# connects to the metaDataStore server
		self.metaDataStore = rpyc.connect(metadata_ip_port.split(':')[0], metadata_ip_port.split(':')[1])
		self.blockStoreList = []
		for n in range(self.no_of_blockstores):
			ip, port = confdict['block'+str(n)].split(':')
			blockStore = rpyc.connect(ip, port)
			self.blockStoreList.append(blockStore)
		self.fileverdict = {}
		self.hash_dict = {}

	"""
	upload(filepath) : Reads the local file, creates a set of
	hashed blocks and uploads them onto the MetadataStore
	(and potentially the BlockStore if they were not already present there).
	"""
	def upload(self, filepath):
		version = 1
		rpath = os.path.realpath(filepath)
		filename = rpath.replace('\\', '/')
		filename = filename.split('/')
		filename = filename[len(filename)-1]
		#print(filename)
		file = open(rpath, 'rb')
		# utf-8 and bytes formatting changes?
		data = file.read()
		file.close()
		# create hashlist
		self.hash_dict = self.hasher(data)
		hash_list = []
		for key, value in self.hash_dict.items():
			hash_list.append(key)
		# we have the hashlist!
		# initial modify (If this works, that means the filename sent is new)
		try:
			# need to put a while loop here
			print(filename)
			missing_hashlist, version = self.metaDataStore.root.modify_file(filename, 1, json.dumps(hash_list))
			if json.loads(missing_hashlist):
				rver = version + 1
				version += 1
				missing_hashlist, version = self.metaDataStore.root.modify_file(filename, version, json.dumps(hash_list))
				if version == rver:
					print("Modified")
		except ErrorResponse as e:
			eprint("Some error happening!")
			print("Not Found")
			# putting missing hashlist in blockstore
		blah = json.loads(missing_hashlist)
		if blah:
			for hash in blah:
				print(blah)
				block_number = self.findServer(hash)
				self.blockStoreList[block_number].root.store_block(hash, self.hash_dict[hash])
			print("OK")
		else:
			print("OK")

	def hasher(self, data):
		hash_dict = {}
		from math import ceil as ceiling
		for x in range(ceiling(len(data)/4096)):
			block = data[4096*x:4096*(x+1)]
			hash = hashlib.sha1(block).hexdigest()
			#print(hash)
			hash_dict.update({hash: block})
		return hash_dict

	"""
	delete(filename) : Signals the MetadataStore to delete a file.
	"""
	def delete(self, filename):
		try:
			hashlist, version = self.metaDataStore.root.read_file(filename)
			hashlist = json.loads(hashlist)
			version += 1 # for the tombstone value
			if not hashlist:
				print("OK")
			else:
				try:
					self.metaDataStore.root.delete_file(filename, version)
					print("OK")
				except:
					eprint(e.argv)
					print("Not Found")
		except:
			print("Not Found")
	"""
        download(filename, dst) : Downloads a file (f) from SurfStore and saves
        it to (dst) folder. Ensures not to download unnecessary blocks.
	"""
	def download(self, filename, location):
		rpath = os.path.realpath(location)
		if os.path.isdir(rpath):
			fil = location + "/" + filename
			fpath = os.path.realpath(fil)
			try:
				hashlist, version = self.metaDataStore.root.read_file(filename)
				hashlist = json.loads(hashlist)
				if hashlist == []:
					raise ErrorResponse("No file")
				final = ""
				for hash in hashlist:
					#print("ye")
					#print(hash)
					block_number = self.findServer(hash)
					block = self.blockStoreList[block_number].root.get_block(hash)
					block = block.decode('utf-8')
					final += block
				fildir = open(fpath, 'w')
				fildir.write(final)
				fildir.close()
				print("OK")
			except ErrorResponse:
				print("Not Found1")

		else:
			print("Not Found2")

	def findServer(self, h):
		return (int(h,16)) % self.no_of_blockstores

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
