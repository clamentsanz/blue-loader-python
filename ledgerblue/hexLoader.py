"""
*******************************************************************************
*   Ledger Blue
*   (c) 2016 Ledger
*
*  Licensed under the Apache License, Version 2.0 (the "License");
*  you may not use this file except in compliance with the License.
*  You may obtain a copy of the License at
*
*      http://www.apache.org/licenses/LICENSE-2.0
*
*  Unless required by applicable law or agreed to in writing, software
*  distributed under the License is distributed on an "AS IS" BASIS,
*  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*  See the License for the specific language governing permissions and
*  limitations under the License.
********************************************************************************
"""

from Crypto.Cipher import AES
import struct
import hashlib
import binascii

LOAD_SEGMENT_CHUNK_HEADER_LENGTH = 3
MIN_PADDING_LENGTH = 1

class HexLoader:
	def __init__(self, card, cla=0xF0, secure=False, key=None, relative=True):
		self.card = card
		self.cla = cla
		self.secure = secure
		self.key = key
		self.iv = b"\x00" * 16
		self.relative = relative

	
		
	def crc16(self, data):
		TABLE_CRC16_CCITT = [
			0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
			0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
			0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
			0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
			0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
			0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
			0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
			0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
			0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
			0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
			0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
			0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
			0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
			0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
			0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
			0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
			0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
			0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
			0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
			0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
			0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
			0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
			0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
			0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
			0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
			0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
			0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
			0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
			0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
			0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
			0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
			0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
		]
		crc =  0xFFFF
		for i in range(0, len(data)):
			b = data[i] & 0xff
			b = (b ^ ((crc >> 8) & 0xff)) & 0xff
			crc = (TABLE_CRC16_CCITT[b] ^ (crc << 8)) & 0xffff
		return crc

	def exchange(self, cla, ins, p1, p2, data):
		apdu = bytearray([cla, ins, p1, p2, len(data)]) + bytearray(data)
		if self.card == None:
			print("%s" % binascii.hexlify(apdu))
		else:
			return self.card.exchange(apdu)

	def encryptAES(self, data):
		if not self.secure:
			return data
		paddedData = data + b'\x80'
		while (len(paddedData) % 16) != 0:
			paddedData += b'\x00'
		cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
		encryptedData = cipher.encrypt(str(paddedData))
		self.iv = encryptedData[len(encryptedData) - 16:]
		return encryptedData

	def decryptAES(self, data):
		if not self.secure or len(data) == 0:
			return data
		cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
		decryptedData = cipher.decrypt(data)
		l = len(decryptedData) - 1
		while (decryptedData[l] != chr(0x80)):
			l-=1
		decryptedData = decryptedData[0:l]
		self.iv = data[len(data) - 16:]
		return decryptedData

	def selectSegment(self, baseAddress):
		data = b'\x05' + struct.pack('>I', baseAddress)
		data = self.encryptAES(data)
		self.exchange(self.cla, 0x00, 0x00, 0x00, data)

	def loadSegmentChunk(self, offset, chunk):
		data = b'\x06' + struct.pack('>H', offset) + chunk
		data = self.encryptAES(data)
		self.exchange(self.cla, 0x00, 0x00, 0x00, data)		

	def flushSegment(self):
		data = b'\x07'
		data = self.encryptAES(data)
		self.exchange(self.cla, 0x00, 0x00, 0x00, data)				

	def crcSegment(self, offsetSegment, lengthSegment, crcExpected):
		data = b'\x08' + struct.pack('>H', offsetSegment) + struct.pack('>I', lengthSegment) + struct.pack('>H', crcExpected)
		data = self.encryptAES(data)
		self.exchange(self.cla, 0x00, 0x00, 0x00, data)						

	def validateTargetId(self, targetId):
		data = struct.pack('>I', targetId)
		self.exchange(self.cla, 0x04, 0x00, 0x00, data)

	def boot(self, bootadr, signature=None):
		# Force jump into Thumb mode
		bootadr |= 1
		data = b'\x09' + struct.pack('>I', bootadr)
		if (signature != None):
			data += chr(len(signature)) + signature
		data = self.encryptAES(data)
		self.exchange(self.cla, 0x00, 0x00, 0x00, data)

	def createApp(self, appflags, applength, appname, icon=None, path=None, iconOffset=None, iconSize=None, appversion=None):
		data = b'\x0B' + struct.pack('>I', applength) + struct.pack('>I', appflags) + struct.pack('>B', len(appname)) + appname
		if iconOffset is None:
			if not (icon is None):
				data += struct.pack('>B', len(icon)) + icon
			else:
				data += b'\x00'

		if not (path is None):
			data += struct.pack('>B', len(path)) + path
		else:
			data += b'\x00'

		if not iconOffset is None:
			data += struct.pack('>I', iconOffset) + struct.pack('>H', iconSize)

		if not appversion is None:
			data += struct.pack('>B', len(appversion)) + appversion

		data = self.encryptAES(data)
		self.exchange(self.cla, 0x00, 0x00, 0x00, data)						

	def deleteApp(self, appname):
		data = b'\x0C' +  struct.pack('>B',len(appname)) +  appname
		data = self.encryptAES(data)
		self.exchange(self.cla, 0x00, 0x00, 0x00, data)						

	def listApp(self, restart=True):
		if restart:
			data = b'\x0E'
		else:
			data = b'\x0F'
		data = self.encryptAES(data)
		response = str(self.exchange(self.cla, 0x00, 0x00, 0x00, data))
		response = bytearray(self.decryptAES(response))
		result = []
		offset = 0
		while offset != len(response):
			item = {}
			offset += 1
			item['name'] = response[offset + 1 : offset + 1 + response[offset]]
			offset += 1 + response[offset]
			item['flags'] = response[offset] << 24 | response[offset + 1] << 16 | response[offset + 2] << 8 | response[offset + 3]
			offset += 4
			item['hash'] = response[offset : offset + 32]
			offset += 32
			result.append(item)
		return result

	def load(self, erase_u8, max_length_per_apdu, hexFile):
		initialAddress = 0
		if self.relative:
			initialAddress = hexFile.minAddr()
		sha256 = hashlib.new('sha256')
		for area in hexFile.getAreas():
			startAddress = area.getStart() - initialAddress
			data = area.getData()
			self.selectSegment(startAddress)
			if len(data) == 0:
				continue
			if len(data) > 0x10000:
				raise Exception("Invalid data size for loader")
			crc = self.crc16(bytearray(data))
			offset = 0
			length = len(data)
			while (length > 0):
				if length > max_length_per_apdu - LOAD_SEGMENT_CHUNK_HEADER_LENGTH - MIN_PADDING_LENGTH:
					chunkLen = max_length_per_apdu - LOAD_SEGMENT_CHUNK_HEADER_LENGTH - MIN_PADDING_LENGTH
				else:
					chunkLen = length
				chunk = data[offset : offset + chunkLen]
				sha256.update(chunk)
				self.loadSegmentChunk(offset, bytes(chunk))
				offset += chunkLen
				length -= chunkLen
			self.flushSegment()
			self.crcSegment(0, len(data), crc)
		return sha256.hexdigest()

	def run(self, hexFile, bootaddr, signature=None):
		initialAddress = 0
		if self.relative:
			initialAddress = hexFile.minAddr()
		self.boot(bootaddr - initialAddress, signature)

	def resetCustomCA(self):
		data = b'\x13'
		data = self.encryptAES(data)
		self.exchange(self.cla, 0x00, 0x00, 0x00, data)

	def setupCustomCA(self, name, public):
		data = b'\x12' + struct.pack('>B',len(name)) + name +  struct.pack('>B',len(public)) + public
		data = self.encryptAES(data)
		self.exchange(self.cla, 0x00, 0x00, 0x00, data)
