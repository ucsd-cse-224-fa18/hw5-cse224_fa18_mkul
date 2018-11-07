import rpyc
import sys
import json
from threading import Lock
'''
A sample ErrorResponse class. Use this to respond to client requests when the request has any of the following issues -
1. The file being modified has missing blocks in the block store.
2. The file being read/deleted does not exist.
3. The request for modifying/deleting a file has the wrong file version.

You can use this class as it is or come up with your own implementation.
'''
class ErrorResponse(Exception):
	def __init__(self, message):
		super(ErrorResponse, self).__init__(message)
		self.error = message

	def missing_blocks(self, hashlist):
		self.error_type = 1
		self.missing_blocks = hashlist

	def wrong_version_error(self, version):
		self.error_type = 2
		self.current_version = version

	def file_not_found(self):
		self.error_type = 3



'''
The MetadataStore RPC server class.

The MetadataStore process maintains the mapping of filenames to hashlists. All
metadata is stored in memory, and no database systems or files will be used to
maintain the data.
'''
class MetadataStore(rpyc.Service):


	"""
        Initialize the class using the config file provided and also initialize
        any datastructures you may need.
		The config file may also be used to create multiple blockstore servers
	"""
	def __init__(self, config):
		self.exposed_fileHash = {} # stores the file: hash list pairs
		confdict = {}
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
		# confdict now only has the values of the blockstore
		del confdict['metadata']
		# connects to the metaDataStore server
		self.blockStoreList = []
		for n in range(self.no_of_blockstores):
			ip, port = confdict['block'+str(n)].split(':')
			blockStore = rpyc.connect(ip, port)
			self.blockStoreList.append(blockStore)
		self.uploadlock = Lock()

		'''
	        ModifyFile(f,v,hl): Modifies file f so that it now contains the
	        contents refered to by the hashlist hl.  The version provided, v, must
	        be exactly one larger than the current version that the MetadataStore
	        maintains.

	        As per rpyc syntax, adding the prefix 'exposed_' will expose this
	        method as an RPC call
		'''
	def exposed_modify_file(self, filename, version, hashlist):
		self.uploadlock.acquire()
		# for already existent files
		hashlist = json.loads(hashlist)
		if filename not in self.exposed_fileHash.keys() and version==1:
			self.create_new_entry(filename, hashlist, version)
			missing_hashlist = self.check_hashlist(filename, hashlist)
			#print("created new entry")
			dump = json.dumps(missing_hashlist)
			self.uploadlock.release()
			return dump, version, True
			#print("LOL?")
		if filename in self.exposed_fileHash.keys(): # check file in dict
			if version == self.exposed_fileHash[filename][0] + 1: # check if version is greater so that it can update
				#print("Modifying the filename")
				missing_hashlist = self.check_hashlist(filename, hashlist)
				self.exposed_fileHash[filename][0] = version
				self.exposed_fileHash[filename][1] = hashlist
				self.uploadlock.release()
				return json.dumps(missing_hashlist), version, False
			else: # if not, send blank hashlist and correct version
				#print("bad version number")
				missing_hashlist = []
				self.uploadlock.release()
				return json.dumps(missing_hashlist), self.exposed_fileHash[filename][0], False

	def check_hashlist(self, filename, hashlist):
		missing_hashlist = []
		for hash in hashlist:
			block_no = self.findServer(hash)
			if not self.blockStoreList[block_no].root.has_block(hash):
				missing_hashlist.append(hash)
		return missing_hashlist

	def create_new_entry(self, filename, hashlist, version):
		#print("Trying entry!")
		self.exposed_fileHash.update({filename:[version, hashlist]})

	'''
        DeleteFile(f,v): Deletes file f. Like ModifyFile(), the provided
        version number v must be one bigger than the most up-date-date version.

        As per rpyc syntax, adding the prefix 'exposed_' will expose this
        method as an RPC call
	'''
	def exposed_delete_file(self, filename, version):
		if version == self.exposed_fileHash[filename][0] + 1:
			if self.exposed_fileHash[filename][1]:
				self.exposed_fileHash[filename][1] = []
				self.exposed_fileHash[filename][0] = version
		else:
			raise ErrorResponse("Wrong Version").wrong_version_error(self.exposed_fileHash[filename][0])

	'''
        (v,hl) = ReadFile(f): Reads the file with filename f, returning the
        most up-to-date version number v, and the corresponding hashlist hl. If
        the file does not exist, v will be 0.

        As per rpyc syntax, adding the prefix 'exposed_' will expose this
        method as an RPC call
	'''
	def exposed_read_file(self, filename):
		# for downloading a file
		try:
			if filename in self.exposed_fileHash.keys():
				version = self.exposed_fileHash[filename][0]
				hashlist = self.exposed_fileHash[filename][1]
				return  (version, hashlist)
			else:
				return (0, [])
		except Exception:
			pass

	def findServer(self, h):
		return (int(h,16)) % self.no_of_blockstores

if __name__ == '__main__':
	from rpyc.utils.server import ThreadPoolServer
	server = ThreadPoolServer(MetadataStore(sys.argv[1]), port = 6000)
	server.start()
