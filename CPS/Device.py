from CPS.AnytoneMemory import AnyToneMemory, Channel
from CPS.Utils import Bit
from serial import Serial
import time
from PySide6.QtSerialPort import QSerialPort
from PySide6.QtCore import QObject, QDeadlineTimer, Signal, QRunnable

def printBytesHex(data):
    print('   | 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f')
    print('----------------------------------------------------')
    for i, b in enumerate(data):
        if i % 16 > 0:
            print(' ', end='')
        elif i != 0:
            print('')
            print(f'{i:02x} | ', end='')
        else:
            print(f'{i:02x} | ', end='')

        
        print(f'{b:02x}', end='')

    print('\n\r')
        
class AnyToneDevice(QObject):
    STATUS_SUCCESS = 0
    STATUS_COM_ERROR = 1
    STATUS_DEVICE_MISMATCH = 2

    finished = Signal(int)
    update1 = Signal(int, int, str)
    update2 = Signal(int, int, str)

    is_alive = False

    verbose = False
    read_write_options: int = 0

    def __init__(self):
        super().__init__()

    def printProgress(self, progress):
        print(str(int(progress)) + '%', '\t[', end='')
        for i in range(100):
            if i < progress:
                print('-', end='')
            elif i == progress:
                print('>', end='')
            else:
                print(' ', end='')
        print(']', end='\r')

    def readMemory(self, start_address, read_len):
        data = b''
        read_count = read_len/0x10
        if self.verbose:
            print("Reading:", hex(start_address), '-', hex(start_address + read_len))
        for idx, addr in enumerate(range(start_address, start_address + read_len, 0x10)):
            progress = round((idx / read_count) * 100, 0)
            if self.verbose:
                self.printProgress(progress)
            data += self.readMemoryAddress(addr, 0x10)[0]

        if self.verbose:
            self.printProgress(100)
            print("")
        return data
    
    def writeMemory(self, address, data):
        pass
    
    def readRadioData(self):
        
        local_info = self.readDeviceInfo()
        if local_info[0] != 'ID878UV2' or local_info[1] != 'V101': # TODO: Update this when adding new models
            self.finished.emit(AnyToneDevice.STATUS_DEVICE_MISMATCH)
            return

        if self.read_write_options == 1 or self.read_write_options == 3:
            self.readOtherData()
        elif self.read_write_options == 2:
            self.readDigitalContacts()

    # Digital Contact
    def readDigitalContacts(self):
        contact_count = int.from_bytes(self.readMemory(0x4840000, 16)[0:4], 'little')
        
        # Read the ID/Group Call and offsets
        # contact_id_data:list[bytes] = []
        # contact_id_list = []
        # offset = 0x4000000
        # for i in range(read_count): #Since there are two contacts per 16 bytes, 
        #                             #read_count is half the contact count rounded up to the nearest 16 bytes

        #                             # Each block of data is 1f400 bytes long

        #     block = int(i/0x1f40)
        #     address = offset + (block * 0x40000) + ((i % 0x1f40) * 16) # Each block is offset by 0x40000

        #     data = self.readMemory(address, 16)
        #     self.update2.emit(i, read_count, 'Order Read')
        #     if data[0] != 0xff:
        #         contact_id_data.append(data[0:8])
        #     if data[8] != 0xff:
        #         contact_id_data.append(data[8:16])
        #     if data[0] == 0xff or data[8] == 0xff:
        #         break

        

        # Format List
        # for i, c in enumerate(contact_id_data):
        #     call_type = Bit.getBit(c[0], 0)
        #     dmr_id = int(hex(int.from_bytes(c[0:4], 'little') >> 1).replace('0x', '')) # 16777215 = All Call
        #     offset = int.from_bytes(c[4:8], 'little')
        #     contact_id_list.append((call_type, dmr_id, offset))

        # contact_data_buffer = bytearray()
        # for i in range(blocks):
        #     address = 0x5500000 + (i * 0x40000)
        #     self.update2.emit(i, blocks, 'Reading Contact Data')
        #     for j in range(0, 0x186a0, 16):
        #         data = self.readMemory(address + j, 16)
        #         if data.startswith(b'\xff'):
        #             break
        #         contact_data_buffer.extend(data)

        contact_data = bytearray()
        offset = 0
        for i in range(contact_count):
            self.update2.emit(i, contact_count, 'Reading Contacts')

            if len(contact_data) - offset < 0x80:
                # print(len(contact_data), offset)
                contact_data.extend(self.getDigitalContactDataBuffer(len(contact_data)))


            dc = AnyToneMemory.digital_contact_list[i]
            dc.id = i

            dc.call_type = contact_data[offset]
            offset += 1

            dc.radio_id = int(contact_data[offset:offset+4].hex())
            offset += 4

            dc.call_alert = contact_data[offset]
            offset += 1

            eos = contact_data.find(b'\x00', offset)
            dc.name = contact_data[offset:eos].decode('utf-8')
            offset = eos + 1

            eos = contact_data.find(b'\x00', offset)
            dc.city = contact_data[offset:eos].decode('utf-8')
            offset = eos + 1

            eos = contact_data.find(b'\x00', offset)
            dc.callsign = contact_data[offset:eos].decode('utf-8')
            offset = eos + 1

            eos = contact_data.find(b'\x00', offset)
            dc.state = contact_data[offset:eos].decode('utf-8')
            offset = eos + 1

            eos = contact_data.find(b'\x00', offset)
            dc.country = contact_data[offset:eos].decode('utf-8')
            offset = eos + 1

            eos = contact_data.find(b'\x00', offset)
            dc.remarks = contact_data[offset:eos].decode('utf-8')
            offset = eos + 1
            
    def getDigitalContactDataBuffer(self, offset) -> bytes:
        data = b''
        if offset % 16 != 0:
            print('Error: Offset alignment')
        
        for i in range(offset, offset + 0x80, 0x10): # This is long enough to fit a digital contact
            addr_mod = i % 0x186a0
            block = int((i - addr_mod) / 0x186a0)
            addr = 0x5500000 + (block * 0x40000) + addr_mod
            # start_addr = 0x5500000 + (block * 0x40000)
            data += self.readMemory(addr, 0x10)

        return data

    # Other Data
    def readOtherData(self):
        AnyToneMemory.init()

        self.update1.emit(0, 8, 'Reading Data')
        self.update2.emit(0, 0, 'Reading Headers')
        data_0 = self.readMemory(0x2640000, 0x4f0) # Talkgroup Set List = 0
        # vfo_a_data = self.readMemory(0xfc0800, 0x80) # VFO Primary Data
        # vfo_b_data = self.readMemory(0xfc2800, 0x80) # VFO Secondary Data
        roaming_zone_set_data = self.readMemory(0x1042000, 0x20) # Roaming Channel Set List = 1 |
        roaming_channel_set_data = self.readMemory(0x1042080, 0x10) # Roaming Zone Set List = 1 |
        # data_5 = self.readMemory(0x1640000, 0x640) # 
        # data_6 = self.readMemory(0x1640800, 0x70) # 
        # data_7 = self.readMemory(0x1640880, 0x10) # 
        fm_data = self.readMemory(0x2480200, 0x30) # FM VFO & Active/Scan
        # data_9 = self.readMemory(0x24c0c80, 0x10) # 
        # data_10 = self.readMemory(0x24c0d00, 0x200) # 
        # data_11 = self.readMemory(0x24c1000, 0xd0) # 
        # data_12 = self.readMemory(0x24c1280, 0x20) # 
        zone_set_data = self.readMemory(0x24c1300, 0x20) # Zone Set List = 1
        radioid_set_data = self.readMemory(0x24c1320, 0x20) # Radio ID Set List = 1
        scanlist_set_data = self.readMemory(0x24c1340, 0x20) # Scan List Set List = 1
        # data_13 = self.readMemory(0x24c1360, 0x20) # ? Set List = 1
        # data_14 = self.readMemory(0x24c1400, 0x20) # 
        # data_15 = self.readMemory(0x24c1440, 0x30) # 
        channel_set_data = self.readMemory(0x24c1500, 0x200) # Channels Exist = 1
        # data_16 = self.readMemory(0x24c1700, 0x40) #
        # data_17 = self.readMemory(0x24c1800, 0x500) # 
        auto_repeater_offset_data = self.readMemory(0x24c2000, 0x3f0) # Auto Repeater Offset Frequencies
        # data_19 = self.readMemory(0x24c2600, 0x10) # 
        # data_20 = self.readMemory(0x24c4000, 0x4000) # 
        optional_settings_data_0000 = self.readMemory(0x2500000, 0xf0) # Optional Settings
        # data_22 = self.readMemory(0x2500100, 0x500) #
        optional_settings_data_0600 = self.readMemory(0x2500600, 0x30) # Optional Settings
        # data_23 = self.readMemory(0x2501000, 0x240) # 
        optional_settings_data_1280 = self.readMemory(0x2501280, 0x20) # Optional Settings
        # data_24 = self.readMemory(0x2501300, 0x10)
        optional_settings_data_1400 = self.readMemory(0x2501400, 0x100) # Optional Settings
        # data_25 = self.readMemory(0x2501500, 0x100) # 
        # data_26 = self.readMemory(0x2501800, 0x100) # 
        gps_roaming_data = self.readMemory(0x2504000, 0x400) # GPS Roaming
        master_radioid_data = self.readMemory(0x2582000, 0x20) # Master Radio ID

        # data_29 = self.readMemory(0x25c0000, 0x860) # 
        # data_30 = self.readMemory(0x25c0b00, 0x30) # 
        # data_31 = self.readMemory(0x25c0c00, 0xff0) # 
        # data_32 = self.readMemory(0x2600000, 0xf0) # 
        # data_33 = self.readMemory(0x2900000, 0x80) # 
        # data_34 = self.readMemory(0x2900100, 0x80) # 
        # data_35 = self.readMemory(0x800000, 0xc40) # Channel Data
        # data_36 = self.readMemory(0x8018c0, 0x1c0) # Channel Data
        # data_37 = self.readMemory(0x802000, 0xc40) # Channel Data
        # data_38 = self.readMemory(0x8038c0, 0x1c0) # Channel Data
        # data_39 = self.readMemory(0x840540, 0x340) # Channel Data
        # data_40 = self.readMemory(0x8411c0, 0x780) # Channel Data
        # data_41 = self.readMemory(0x842540, 0x340) # Channel Data
        # data_42 = self.readMemory(0x8431c0, 0x780) # Channel Data
        # data_43 = self.readMemory(0x880480, 0x300) # Channel Data
        # data_44 = self.readMemory(0x880ac0, 0x540) # Channel Data
        # data_45 = self.readMemory(0x882480, 0x300) # Channel Data
        # data_46 = self.readMemory(0x882ac0, 0x540) # Channel Data
        # data_47 = self.readMemory(0x1000000, 0x1000) # 
        # data_48 = self.readMemory(0x1040000, 0x20) # Roam Channel Data
        # data_49 = self.readMemory(0x1043000, 0x80) #
        # data_50 = self.readMemory(0x1080000, 0x90) #
        # data_51 = self.readMemory(0x1080200, 0x90) #
        # data_52 = self.readMemory(0x1080600, 0x90) #
        # data_53 = self.readMemory(0x2140000, 0x500) #
        # data_54 = self.readMemory(0x2480000, 0x10) # FM Frequencies
        # data_55 = self.readMemory(0x24c2400, 0x20) #
        # data_56 = self.readMemory(0x2540000, 0x100) # Zone Names
        # data_57 = self.readMemory(0x2580000, 0x40) #
        # data_58 = self.readMemory(0x2680000, 0x1650) #
        

        AnyToneMemory.optional_settings.decode(optional_settings_data_0000, optional_settings_data_0600, optional_settings_data_1280, optional_settings_data_1400)

        if not self.is_alive:
            return self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
        # Create Prefab SMS List
        sms_index_list = []
        current_index = 0
        while(current_index < 101):
            addr = 0x1640000 + (current_index * 0x10)
            sms_data = self.readMemory(addr, 0x10)
            if sms_data[3] == 0xff:
                break
            sms_index_list.append(sms_data[3])
            if sms_data[2] == 0xff:
                break
            current_index = sms_data[2]

        # Create Roaming Channel Index List
        roaming_channel_index_list = []
        for byte_idx, data_byte in enumerate(roaming_channel_set_data):
            for bit_index in range(8):
                bit_set = Bit.getBit(data_byte, bit_index)
                if bit_set:
                    roaming_channel_index_list.append((byte_idx * 8) + bit_index)

        # Create Roaming Zone Index List
        roaming_zone_index_list = []
        for byte_idx, data_byte in enumerate(roaming_zone_set_data):
            for bit_index in range(8):
                bit_set = Bit.getBit(data_byte, bit_index)
                if bit_set:
                    roaming_zone_index_list.append((byte_idx * 8) + bit_index)

        # Create TG Index List
        talkgroup_set_data = data_0[:0x4e2]
        talkgroup_index_list = []
        for byte_idx, data_byte in enumerate(talkgroup_set_data):
            for bit_index in range(8):
                bit_set = not Bit.getBit(data_byte, bit_index)
                if bit_set:
                    talkgroup_index_list.append((byte_idx * 8) + bit_index)

        # Create Zone Index List
        zone_index_list = []
        for byte_idx, data_byte in enumerate(zone_set_data):
            for bit_index in range(8):
                bit_set = Bit.getBit(data_byte, bit_index)
                if bit_set:
                    zone_index_list.append((byte_idx * 8) + bit_index)
        
        # Create Channel Index List
        channel_set_data = channel_set_data[:0x1fa]
        channel_index_list = []
        for byte_idx, data_byte in enumerate(channel_set_data):
            for bit_index in range(8):
                bit_set = Bit.getBit(data_byte, bit_index)
                if bit_set:
                    channel_index_list.append((byte_idx * 8) + bit_index)

        # Create Radio ID Index List
        radioid_index_list = []
        for byte_idx, data_byte in enumerate(radioid_set_data):
            for bit_index in range(8):
                rid_index = (byte_idx * 8) + bit_index
                if rid_index < 250:
                    bit_set = Bit.getBit(data_byte, bit_index)
                    if bit_set:
                        radioid_index_list.append(rid_index)

        # Create Radio ID Index List
        scan_list_index_list = []
        for byte_idx, data_byte in enumerate(scanlist_set_data):
            for bit_index in range(8):
                sl_index = (byte_idx * 8) + bit_index
                if sl_index < 250:
                    bit_set = Bit.getBit(data_byte, bit_index)
                    if bit_set:
                        scan_list_index_list.append(sl_index)
        
        
        if not self.is_alive:
            self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            return
        
        # Read Roaming Channel Data
        self.update1.emit(1, 8, 'Reading Data')
        self.readRoamingChannelData(roaming_channel_index_list)

        # Read Roaming Zone Data
        self.update1.emit(1, 8, 'Reading Data')
        self.readRoamingZoneData(roaming_zone_index_list)

        # Read TalkGroup Data
        self.update1.emit(1, 8, 'Reading Data')
        self.readTalkGroupData(talkgroup_index_list)
        if not self.is_alive:
            self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            return

        # Read Channel Data
        self.update1.emit(2, 8, 'Reading Data')
        self.readRadioChannelData(channel_index_list)
        if not self.is_alive:
            self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            return

        # Read Zone Data 
        self.update1.emit(3, 8, 'Reading Data')
        self.readZoneData(zone_index_list)
        if not self.is_alive:
            self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            return

        # Read Radio ID Data
        self.update1.emit(4, 8, 'Reading Data')
        self.readRadioIdData(radioid_index_list)
        if not self.is_alive:
            self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            return

        # Read Scan List Data
        self.update1.emit(5, 8, 'Reading Data')
        self.readScanListData(scan_list_index_list)
        if not self.is_alive:
            self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            return

        # Master Radio ID
        self.update1.emit(6, 8, 'Reading Data')
        AnyToneMemory.master_radioid.decode(master_radioid_data)
        if not self.is_alive:
            self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            return
        
        # Auto Repeater Offset Data
        self.update1.emit(7, 8, 'Reading Data')
        self.readAutoRepeaterFrequencyData(auto_repeater_offset_data)
        if not self.is_alive:
            self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            return

        # FM Data
        self.update1.emit(8, 8, 'Reading Data')
        self.readFM(fm_data)

        # SMS Data
        self.update1.emit(9, 8, 'Reading Data')
        self.readPrefabSms(sms_index_list)

        # GPS Roaming
        self.update1.emit(8, 8, 'Reading Data')
        for gps_idx in range(32):
            self.update2.emit(gps_idx, 32, 'Reading GPS Roaming')
            gps_addr = (gps_idx % 16) * 0x20
            if gps_idx >= 16:
                gps_addr += 0x10
            gdata = gps_roaming_data[gps_addr:gps_addr+0x10]
            AnyToneMemory.gps_roaming_list[gps_idx].decode(gdata)

        if not self.is_alive:
            self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            return
        # self.update1.emit(2, 3, 'Parsing Data')
        self.update1.emit(9, 8, 'Data Linking')
        self.update2.emit(0, 0, '')

        AnyToneMemory.linkReferences()

    def readRoamingChannelData(self, index_list: list[int]):
        offset = 0x1040000
        for i, idx in enumerate(index_list):
            self.update2.emit(i, len(index_list), 'Reading Roaming Channels')
            addr = offset + (idx * 0x20)
            data = self.readMemory(addr, 0x20)
            if not self.is_alive:
                self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            AnyToneMemory.roaming_channels[idx].decode(data)

    def readRoamingZoneData(self, index_list: list[int]):
        offset = 0x1043000
        for i, idx in enumerate(index_list):
            self.update2.emit(i, len(index_list), 'Reading Roaming Zones')
            addr = offset + (idx * 0x50)
            data = self.readMemory(addr, 0x50)
            if not self.is_alive:
                self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            AnyToneMemory.roaming_zones[idx].decode(data)

    def readAutoRepeaterFrequencyData(self, data: bytes):
        for i in range(250):
            self.update2.emit(i, 250, 'Reading Auto Repeater Frequencies')
            arf = AnyToneMemory.auto_repeater_freq_list[i]
            addr = i*4
            arf.frequency = int.from_bytes(data[addr:addr+4], 'little')
        
    def readRadioChannelData(self, index_list: list[int]):
        offset = 0x800000
        for i, idx in enumerate(index_list):
            self.update2.emit(i, len(index_list), 'Reading Channels')
            channel_data_block = int(idx / 128)
            primary_data_address = offset + ((idx - (channel_data_block * 128)) * 0x40) + (channel_data_block * 0x40000)
            secondary_data_address = primary_data_address + 0x2000
            
            channel_primary_data = self.readMemory(primary_data_address, 0x40)
            channel_secondary_data = self.readMemory(secondary_data_address, 0x40)

            if not self.is_alive:
                self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)

            AnyToneMemory.channels[idx].decode(channel_primary_data, channel_secondary_data)

    def readTalkGroupData(self, index_list: list[int]):
        offset = 0x2680000
        for i, idx in enumerate(index_list):
            self.update2.emit(i, len(index_list), 'Reading TalkGroups')
            addr = offset + (idx * 0x64)
            tg_data = self.readMemory(addr, 0x40)
            if not self.is_alive:
                self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            AnyToneMemory.talkgroups[idx].decode(tg_data)

    def readZoneData(self, index_list: list[int]):
        zone_name_offset = 0x2540000
        zone_channel_offset = 0x1000000
        zone_a_channel_offset = 0x2500100
        zone_b_channel_offset = 0x2500300
        zone_hide_offset = 0x24c1360

        zone_a_channel_data = self.readMemory(zone_a_channel_offset, 0x200)
        zone_b_channel_data = self.readMemory(zone_b_channel_offset, 0x200)
        zone_hide_data = self.readMemory(zone_hide_offset, 0x20)

        for i, idx in enumerate(index_list):
            self.update2.emit(i, len(index_list), 'Reading Zones')
            if idx < 250:
                # Name
                addr = zone_name_offset + (idx * 0x20)
                zone_name_data = self.readMemory(addr, 0x10)
                if not self.is_alive:
                    return
                AnyToneMemory.zones[idx].name = zone_name_data.decode('utf-8').rstrip('\x00')
                
                # Channels
                addr = zone_channel_offset + (idx * 0x200)
                zone_channel_list_data = self.readMemory(addr, 0x200)
                for i in range(0, len(zone_channel_list_data), 2):
                    ch_idx = int.from_bytes(zone_channel_list_data[i:i+2], 'little')
                    if ch_idx != 0xffff:
                        AnyToneMemory.zones[idx].temp_member_channels.append(ch_idx)

                # A Channel
                AnyToneMemory.zones[idx].a_channel = int.from_bytes(zone_a_channel_data[idx * 2: idx * 2 + 2], 'little')

                # # B Channel
                AnyToneMemory.zones[idx].b_channel = int.from_bytes(zone_b_channel_data[idx * 2: idx * 2 + 2], 'little')
                AnyToneMemory.zones[idx].hide = Bit.getBit(zone_hide_data[int(idx/8)], idx % 8)

    def readRadioIdData(self, index_list: list[int]):
        offset = 0x2580000
        for i, idx in enumerate(index_list):
            self.update2.emit(i, len(index_list), 'Reading Radio IDs')
            addr = offset + (idx * 0x20)
            radioid_data = self.readMemory(addr, 0x20)
            if not self.is_alive:
                self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            AnyToneMemory.radioid_list[idx].decode(radioid_data)

    def readScanListData(self, index_list: list[int]):
        offset = 0x1080000
        for i, idx in enumerate(index_list):
            self.update2.emit(i, len(index_list), 'Reading Scan Lists')
            addr = offset + (idx * 0x200)
            scan_list_data = self.readMemory(addr, 0x90)[:0x83]
            if not self.is_alive:
                self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            AnyToneMemory.scanlist[idx].decode(scan_list_data)

    def readFM(self, fm_data: bytes):
        AnyToneMemory.fm_channels[-1].frequency = int(fm_data[0:4].hex())
        fm_freq_data = bytearray(400)
        read_line_list = []
        for byte_idx in range(16):
            self.update2.emit(byte_idx, 16, 'Reading FM Channels')
            active_byte = fm_data[0x10 + byte_idx]
            scan_byte = fm_data[0x20 + byte_idx]
            for bit_index in range(8):
                fm_index = (byte_idx * 8) + bit_index
                is_active = Bit.getBit(active_byte, bit_index)
                if is_active:
                    scan_add = Bit.getBit(scan_byte, bit_index)
                    if fm_index not in read_line_list:
                        read_line_idx = fm_index % 4
                        read_line_list.append(read_line_idx)
                        fm_freq_data[read_line_idx:read_line_idx+0x10] = bytearray(self.readMemory(0x2480000 + (read_line_idx * 16), 0x10))
                    fm_ch = AnyToneMemory.fm_channels[fm_index]
                    fm_ch.scan_add = scan_add
                    fm_ch.frequency = int(fm_freq_data[fm_index*4:(fm_index*4) + 4].hex())

    def readPrefabSms(self, index_list: list[int]):
        offset = 0x2140000
        for i, idx in enumerate(index_list):
            self.update2.emit(i, len(index_list), 'Reading Scan Lists')
            block = int(((idx * 0x100) - idx % 0x800) / 0x800)
            addr = offset + (block * 0x40000) + ((idx * 0x100) % 0x800)
            sms_data = self.readMemory(addr, 0xd0)
            if not self.is_alive:
                self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
            AnyToneMemory.prefabricated_sms_list[idx].decode(sms_data)

class AnyToneVirtualDevice(AnyToneDevice):
    verbose = False
    serial_port = None

    # Data BIN Size
    # Other Data        0x48001d0
    # Digital Contacts  0x
    bin_data = bytearray([0xff] * 0x48001D0)
    # contact_bin_data = bytearray([0xff] * 0x48001D0)
    is_open = True

    read_dump = ''
    address_blocks = ''
    command_list = []
    last_block_start = 0
    last_addr = 0

    max_address = 0

    def startSerial(self, comport):
        try:
            self.serial_port = Serial(comport, 9600)
        except:
            print('ERR: Could not open port ' + comport)

        while(self.is_open):
            self.readSerial()

    def loadBin(self, filename):
        with open(filename, "rb") as file:
            self.is_alive = True
            self.bin_data = file.read()

    def saveBin(self, filename):
        with open(filename, "wb") as file:
            file.write(self.bin_data)

    def readMemoryAddress(self, address, length):
        data = self.bin_data[address: address + length]
        return [data, len(data)]

    def readSerial(self):
        if self.serial_port == None:
            print("Serial port not set")
            return
        
        data = b''
        while self.serial_port.in_waiting > 0:
            data += self.serial_port.read()

        if len(data) > 0:
            address = 0
            command = b''

            self.command_list.append(data)

            # Read FW Version
            if data == b'R\x02\xfa\x00\x20\x10':
                command = b'W\x02\xfa\x00\x20\x10\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x24\x06'
            
            # Write to Radio
            elif(data.startswith(b'W')):
                address += (data[1] << 24) + (data[2] << 16) + (data[3] << 8) + data[4]
                data_length = data[5]
                rdata = data[6:-2]
                checksum = data[-1]

                if address > self.max_address:
                    self.max_address = address

                if self.last_addr > address or address != self.last_addr + 0x10:
                    self.address_blocks += 'W ' + hex(self.last_block_start) + ' - ' + hex(self.last_addr + 16 - self.last_block_start) + '\r' # + ' ' + hex(self.last_addr+16) + '\r'
                    self.last_block_start = address

                self.last_addr = address

                # if address + 0x10 <= len(self.bin_data):
                # if address < 0x4000000:
                for i, b in enumerate(bytearray(rdata)):
                    self.bin_data[address + i] = b
                # else:
                #     for i, b in enumerate(bytearray(rdata)):
                #         self.contact_bin_data[address - 0x4000000 + i] = b

                command = b'\x06'

            # Read from Radio
            elif(data.startswith(b'R')):
                address += (data[1] << 24) + (data[2] << 16) + (data[3] << 8) + data[4]
                data_length = data[5]

                if address > self.max_address:
                    self.max_address = address

                if self.last_addr > address or address != self.last_addr + 0x10:
                    self.address_blocks += 'R ' + hex(self.last_block_start) + ' - ' + hex(self.last_addr + 16 - self.last_block_start) + '\r' # + ' ' + hex(self.last_addr+16) + '\r'
                    self.last_block_start = address
                # self.read_dump += hex(address) + ' ' + str(data_length) + '\r'

                self.last_addr = address

                command = b'W' + data[1:]
                command += self.bin_data[address:address + data_length]
                checksum = sum(command[1:]) & 0xff
                command += checksum.to_bytes(1, 'big') + b'\x06'

            elif data == b'\x02':
                command = b'ID878UV2\x00V\x31\x30\x31\x00\x00\x06'
            elif data == b'PROGRAM':
                if self.verbose:
                    print("START PC MODE")
                command = b'QX\x06'
            elif data == b'END':
                if self.verbose:
                    print("END PC MODE")
                command = b'\x06'
                self.is_open = False
                self.address_blocks += hex(self.last_block_start) + ' - ' + hex(self.last_addr+16)
                print("MAX Address:", hex(self.max_address + 0x10))

            # print(command)
            self.serial_port.write(command)

    def startProgMode(self):
        if self.serial_port != None:
            self.serial_port.write(b'PROGRAM')

            resp = self.serial_port.read()
            while self.serial_port.in_waiting > 0:
                resp += self.serial_port.read()

            if resp != b'QX\x06' and resp != b'\x06':
                print ('ERR: Unexpected response from device (' + str(resp) + ')' )
                exit()
            else:
                print('PC Mode ok.')
        else:
            print('PC Mode ok.')

    def endProgMode(self):
        if self.serial_port != None:
            # leave pc mode
            self.serial_port.write(b'END')

            resp = self.serial_port.read()
            while self.serial_port.in_waiting > 0:
                resp += self.serial_port.read()

            if resp != b'\x06':
                print ('ERR: Unexpected response from device (' + str(resp) + ')' )
                exit()

    def readLocalInfo(self, extended=False):
        return ''
    
    def readDeviceInfo(self):
        return ('ID878UV2', 'V101')
    
class AnyToneSerial(AnyToneDevice):
    serial_port = None
    device_info = (b'', b'')

    max_bytes_per_read_message = 16 # Anytone CPS uses 16, up to 255 possible
    max_bytes_per_write_message = 16 # Anytone CPS uses 16, more possible?

    def connect(self, portname: str, baud=921600):
        self.serial_port = QSerialPort()
        self.serial_port.setPortName(portname)
        self.serial_port.setBaudRate(baud)
        # self.serial_port.readyRead.connect(self.readyRead)

        
        if self.serial_port.open(QSerialPort.ReadWrite):
            self.is_alive = True
            if self.startProgMode():
                return True
            else:
                self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)
        else:
            print("COM Error: Could not access com port")
        return False

    def read_blocking(self, timeout_ms=1000):
        timer = QDeadlineTimer(timeout_ms)
        data = b""

        while timer.hasExpired() is False:
            if self.serial_port.waitForReadyRead(50):
                data += bytes(self.serial_port.readAll())
                if data.endswith(b"\x06"):  # your completion condition
                    break

        if data == b'':
            is_alive = False

        return data
    
    def startProgMode(self):
        self.serial_port.write(b'PROGRAM')

        resp = self.read_blocking()

        if resp != b'QX\x06' and resp != b'\x06':
            print ('ERR: Unexpected response from device (' + str(resp) + ')' )
            return False
        return True

    def endProgMode(self):
        # leave pc mode
        self.serial_port.write(b'END')

        resp = self.read_blocking()

        if resp != b'\x06':
            print ('ERR: Unexpected response from device (' + str(resp) + ')' )

    def startUpdateMode(self):

        # change to update mode
        self.serial_port.write(b'UPDATE')

        resp = self.serial_port.read()
        while self.serial_port.in_waiting > 0:
            resp += self.serial_port.read()
        if resp != b'\x06':
            print ('ERR: Unexpected response from device (' + str(resp) + ')' )
            exit()

    def endUpdateMode(self):

        # leave pc mode
        self.serial_port.write(b'\x18')

        resp = self.serial_port.read()
        while self.serial_port.in_waiting > 0:
            resp += self.serial_port.read()

        if resp != b'\x06':
            print ('ERR: Unexpected response from device (' + str(resp) + ')' )
            exit()

    def closeDevice(self):
        # close serial port   
        self.serial_port.close()
    
    def readLocalInfo(self, extended=False):
        start_address = 0x2fa0000
        read_len = 0x100
        if extended:
            read_len = 0x40000
        info = self.readMemory(start_address, read_len)
        return info
    
    def readDeviceInfo(self):
        self.serial_port.write(b'\x02')
        resp = self.read_blocking()
        
        # return devicename and version
        device_info =  ( resp[0:8].decode('utf-8').rstrip('\x00'), resp[9:14].decode('utf-8').rstrip('\x00'))
        return device_info
    
    def prinDebugMessage(self, message):
        if len(message) > 8: # 1 byte command + 4 byte address + 1 byte length + 1 byte checksum + 1 byte ACK
            # at least 1 byte data present

            print( message[0:1].hex() + ' | ' + message[1:5].hex() + ' | ' + message[5:6].hex() + ' || ', end = '' )


            # print data as hex
            startdata = 6
            enddata = len(message) - 3
            
            i = startdata
            j = 0
            while i <= enddata:
                print('{0:0{1}x}'.format(message[i],2), end = '')
                if j == 3:
                    print(' ' , end = '')
                    j = 0
                else:
                    j += 1
                i += 1

            # print checksum and ack
            print ( '| ' + message[enddata+1:enddata+2].hex() + ' ' + message[enddata+2:enddata+3].hex() + ' || ', end = '' )

            # print data as ascii with spaces
            i = startdata
            j = 0
            while i <= enddata:
                idec = message[i]
                if (32 <= idec and idec < 127) or (160 <= idec):
                    print( chr(idec), end = '')
                else:
                    print('.', end = '')
                if j == 3:
                    print(' ' , end = '')
                    j = 0
                else:
                    j += 1
                i += 1

            print('|| ', end = '')

            # print data as ascii without spaces
            i = startdata
            while i <= enddata:
                idec = message[i]
                if (32 <= idec and idec < 127) or (160 <= idec):
                    print( chr(idec), end = '')
                else:
                    print('.', end = '')
                i += 1

            print(' || ', end = '')


        print()

    def readMemoryAddress(self, address, num_bytes_left):
        if num_bytes_left % 16 != 0:
            print('Error: Memory Alignment')
        if not self.is_alive:
            return [b'', 0]
        
        resp = bytearray()
            
        while num_bytes_left > 0:
        
            #print(num_bytes_left) # debug
        
            num_bytes = min(num_bytes_left, self.max_bytes_per_read_message)
        
            readcmd = bytearray()
            readcmd.append( ord('R') )
            readcmd.append( (address & 0xff000000) >> 24 )
            readcmd.append( (address & 0x00ff0000) >> 16 )
            readcmd.append( (address & 0x0000ff00) >> 8 )
            readcmd.append( (address & 0x000000ff) )
            readcmd.append( num_bytes )
        
            self.serial_port.write(readcmd)
        
            # message = bytearray()
            # message.append( ord(self.serial_port.read()) )
            # while self.serial_port.in_waiting > 0:
            #     message.append( ord(self.serial_port.read()) )

            message = self.read_blocking()
            if len(message) < 24:
                self.is_alive = False
                return [b'', 0]
            
            checksum = sum(message[1:-2]) & 0xff

            # if ( self.printDebug != 0):
            #     self.printDebugMessage(message)
            
            # check response      
            if message[-2] != checksum:
                print('WARN: Checksum failed. Retransmitting at ' + str(address) )
                continue
            elif message[0] != ord('W'):
                print('WARN: First byte of response not "W": ' + hex(message[0]) + ' Retransmitting at ' + str(address) )
                continue
            elif message[-1] != 0x06:
                print('WARN: Last byte of response not 0x06. Retransmitting at ' + str(address) )
                continue
                
            # message ok.   
            num_bytes_left -= num_bytes
            address += num_bytes

            # save payload only (skip 'W' + 4 bytes address + 1 byte length, cut checksum and ack)
            resp = resp + message[6:-2]
        
        return [resp, len(resp)]

    def writeMemoryAddress(self, address, data):
        if len(data) % 16 != 0:
            print('Error: Memory Alignment')

        num_bytes_left = len(data)
        dataptr = 0
            
        while num_bytes_left > 0:
        
            #print(num_bytes_left) # debug
        
            num_bytes = min(num_bytes_left, self.max_bytes_per_write_message)
            
            while num_bytes_left < self.max_bytes_per_write_message:
                # pad with zeros to reach at least 16 bytes per message
                data.append(0)
                num_bytes_left += 1
                num_bytes += 1
                
        
            # 57 | 05ccab80 | 10 || ffffffff ffffffff ffffffff ffffffff | fc 06 
            writecmd = bytearray()
            writecmd.append( ord('W') )
            writecmd.append( (address & 0xff000000) >> 24 )
            writecmd.append( (address & 0x00ff0000) >> 16 )
            writecmd.append( (address & 0x0000ff00) >> 8 )
            writecmd.append( (address & 0x000000ff) )
            writecmd.append( num_bytes )
            
            i = 0
            while i < num_bytes:
                writecmd.append( data[dataptr+i] )
                i += 1

            checksum = sum(writecmd[1:]) & 0xff
            writecmd.append( checksum )
            writecmd.append( 0x06 )        
            
            self.printDebugMessage(writecmd)

            self.serial_port.write(writecmd)
        
            # read answer
            answ = bytearray()
            answ.append( ord(self.serial_port.read()) )
            while self.serial_port.in_waiting > 0:
                answ.append( ord(self.serial_port.read()) )
            
            if answ[0] == 0x06:
                # ack received, ok
                num_bytes_left -= num_bytes
                dataptr += num_bytes
                address += num_bytes
            else:
                # no response. write again
                print('WARN: No response on write request. Retransmitting at ' + str(address) )
            
    def writeMemoryHex(self, address, hexdata):
        data = bytes.fromhex(hexdata)
        
        num_bytes_left = len(data)
        dataptr = 0
            
        while num_bytes_left > 0:
        
            #print(num_bytes_left) # debug
        
            num_bytes = min(num_bytes_left, self.max_bytes_per_write_message)
        
            # 57 | 05ccab80 | 10 || ffffffff ffffffff ffffffff ffffffff | fc 06 
            writecmd = bytearray()
            writecmd.append( ord('W') )
            writecmd.append( (address & 0xff000000) >> 24 )
            writecmd.append( (address & 0x00ff0000) >> 16 )
            writecmd.append( (address & 0x0000ff00) >> 8 )
            writecmd.append( (address & 0x000000ff) )
            writecmd.append( num_bytes )

            i = 0
            while i < num_bytes:
                writecmd.append( data[dataptr+i] )
                i += 1

            checksum = sum(writecmd[1:]) & 0xff
            writecmd.append( checksum )
            writecmd.append( 0x06 )
            
            
            self.printDebugMessage(writecmd)

            self.serial_port.write(writecmd)
        
            # read answer
            answ = bytearray()
            answ.append( ord(self.serial_port.read()) )
            while self.serial_port.in_waiting > 0:
                answ.append( ord(self.serial_port.read()) )
            
            if answ[0] == 0x06:
                # ack received, ok
                num_bytes_left -= num_bytes
                dataptr += num_bytes
                address += num_bytes
            else:
                # no response. write again
                print('WARN: No response on write request. Retransmitting at ' + str(address) )
            
    def writeRawHex(self, hexline):
        # write raw and already complete hex string to radio
        # warning: no checks!

        data = bytes.fromhex(hexline)

        self.serial_port.write(data)

        # read answer
        answ = bytearray()
        answ.append( ord(self.serial_port.read()) )
        while self.serial_port.in_waiting > 0:
            answ.append( ord(self.serial_port.read()) )

        if answ[0] == 0x06:
            # ack received, ok
            pass
        else:
            # no response. write again
            print('WARN: No response on write request. Retransmitting not implemented. FIXME' )

    def testBaseband(self, retry=True):
        if retry:
            print("Testing baseband.")
        self.serial_port.write(b'\x84\xa9\x61\x00\x02\x00\x16\x00')
        print("Waiting for response")

        data = b''
        time.sleep(1)
        while self.serial_port.in_waiting > 0:
            data += self.serial_port.read()

        if len(data) == 0:
            print("Error: No response from baseband")
            if retry:
                self.testBaseband(False)
        elif data == b'\x84\xa9\x61\x00\x02\x00\x16\x00':
            print("Baseband Active")
        else:
            print("Unknown response:", data)

class AnyToneSerialSignals(QObject):
    finished = Signal(int)
    update1 = Signal(int, int, str)
    update2 = Signal(int, int, str)

class AnyToneSerialWorker(QRunnable):
    signals = AnyToneSerialSignals()
    read_write_options: int = 0
    comport = None
    connection_attempt = 0
    def setComport(self, comport: str):
        self.comport = comport

    def setVirtualFile(self, bin_file: str):
        self.bin_file = bin_file

    def setReadWriteOptions(self, read_write_options: int):
        self.read_write_options = read_write_options

    def run(self):
        if self.comport != None:
            self.radio_device = AnyToneSerial()
            self.radio_device.read_write_options = self.read_write_options
            self.radio_device.update1.connect(self.signals.update1)
            self.radio_device.update2.connect(self.signals.update2)
            self.radio_device.finished.connect(self.signals.finished)

            while(not self.radio_device.is_alive and self.connection_attempt < 5):
                self.connection_attempt += 1
                if self.radio_device.connect(self.comport):
                    self.radio_device.readRadioData()
                    if self.radio_device.is_alive:
                        self.radio_device.endProgMode()
                if not self.radio_device.is_alive:
                    time.sleep(1)

            if self.radio_device.is_alive:
                self.signals.finished.emit(AnyToneDevice.STATUS_SUCCESS)
            else:
                self.signals.finished.emit(AnyToneDevice.STATUS_COM_ERROR)

        elif self.bin_file != None:
            self.radio_device = AnyToneVirtualDevice()
            self.radio_device.read_write_options = self.read_write_options
            self.radio_device.update1.connect(self.signals.update1)
            self.radio_device.update2.connect(self.signals.update2)
            self.radio_device.finished.connect(self.signals.finished)
            self.radio_device.loadBin(self.bin_file)
            self.radio_device.readRadioData()
            self.signals.finished.emit(AnyToneDevice.STATUS_SUCCESS)
