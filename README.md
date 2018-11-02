# CSE 224 Homework 5

Basic starter code for Homework 5

Use the following commands to run the blockstore, metadata store and the client -

1. Blockstore -

   ```shell
   python blockstore.py <port-number>
   ```

2. Metadata store -

   ```shell
   python metastore.py config.txt
   ```

3. Client -

   ```shell
   // to download a file
   python client.py config.txt download myfile.jpg folder_name/

   // to upload a file
   python client.py config.txt upload myfile.jpg

   // to delete a file
   python client.py config.txt delete myfile.jpg
   ```

# Implementation

  For creating a key-pair value we will be creating a memory dictionary in
  blockstore which will store the hash-block in a key-value pair.
  Along with this, the MetadataStore will also have a dict having the
  <filename> : <hash list> dictionary which will be used to add, remove and
  modify the content of the files.
