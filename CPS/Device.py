from CPS.AnytoneMemory import AnyToneMemory, Channel
from CPS.Utils import Bit
from serial import Serial
import time, os
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
    # Read Write Options
    RADIO_DATA = 1
    DIGITAL_CONTACTS = 2
    RADIO_DATA_CONTACTS = 3
    BOOT_IMAGE = 4
    BK1_IMAGE = 5
    BK2_IMAGE = 6

    STATUS_SUCCESS = 0
    STATUS_COM_ERROR = 1
    STATUS_DEVICE_MISMATCH = 2

    finished = Signal(int)
    update1 = Signal(int, int, str)
    update2 = Signal(int, int, str)

    is_alive = False

    verbose = False
    read_write_options: int = 0
    image_data = b''

    def __init__(self):
        super().__init__()

    # Write Memory Functions
    def writeMemory(self, address: int, data: bytes):
        data_len = len(data)
        for idx, addr in enumerate(range(address, address + data_len, 0x10)):
            self.writeMemoryAddress(addr, data[idx * 0x10: (idx * 0x10) + 0x10])

        return data
    
    def writeRadioData(self):
        local_info = self.readDeviceInfo()
        if local_info[0] != 'ID878UV2' or local_info[1] != 'V101': # TODO: Update this when adding new models
            self.finished.emit(AnyToneDevice.STATUS_DEVICE_MISMATCH)
            return

        if self.read_write_options == AnyToneDevice.RADIO_DATA or self.read_write_options == AnyToneDevice.RADIO_DATA_CONTACTS:
            self.writeOtherData()
        elif self.read_write_options == AnyToneDevice.DIGITAL_CONTACTS:
            self.writeDigitalContacts()
        elif self.read_write_options == AnyToneDevice.BOOT_IMAGE:
            self.writeBootImage()
        elif self.read_write_options == AnyToneDevice.BK1_IMAGE:
            self.writeBk1Image()
        elif self.read_write_options == AnyToneDevice.BK2_IMAGE:
            self.writeBk2Image()

    def writeBootImage(self):
        if len(self.image_data) != 0xa000:
            print("Error: Incorrect image data size")
            return
        
        for i in range(0, 0xa000, 0x10):
            self.writeMemory(0x2ac0000 + i, self.image_data[i:i+0x10])
            self.update1.emit(i, 0, '')

    def writeBk1Image(self):
        print('bk1')
        if len(self.image_data) != 0xa000:
            print("Error: Incorrect image data size")
            return
        
        for i in range(0, 0xa000, 0x10):
            self.writeMemory(0x2b00000 + i, self.image_data[i:i+0x10])
            self.update1.emit(i, 0, '')

    def writeBk2Image(self):
        print('bk2')
        if len(self.image_data) != 0xa000:
            print("Error: Incorrect image data size")
            return
        
        for i in range(0, 0xa000, 0x10):
            self.writeMemory(0x2b80000 + i, self.image_data[i:i+0x10])
            self.update1.emit(i, 0, '')
    
    def writeDigitalContacts(self):
        pass
    
    def writeOtherData(self):
        self.radio_write_headers = []
        self.radio_write_data = []
        self.writeTalkgroupData()
        self.writeRadioIdData()
        self.writeZoneData()
        self.writeScanListData()
        self.writeChannelData()
        # self.writeFMChannelData()
        # self.writeGpsRoamingData()
        # self.writeAutoRepeaterFrequencyData()
        # self.writeRoamingChannelData()
        # self.writeRoamingZoneData()
        # self.writeSettingsData()
        # self.writeMasterRadioIdData()

        # self.radio_write_data.sort(key=lambda x: x[0])
        self.update1.emit(0, len(self.radio_write_data) + 1, 'Writing Headers')
        for i, (addr, data) in enumerate(self.radio_write_headers):
            self.update2.emit(i, len(self.radio_write_data) + 1, 'Writing Headers')
            self.writeMemory(addr, data)


        for i, (desc, write_list) in enumerate(self.radio_write_data):
            self.update1.emit(i+1, len(self.radio_write_data) + 1, 'Writing Data')
            write_list.sort(key=lambda x: x[0])
            for j, (addr, data) in enumerate(write_list):
                if desc == 'Writing Zone Data':
                    print(desc, hex(addr), hex(len(data)))
                self.update2.emit(j, len(write_list), desc)
                self.writeMemory(addr, data)

    def writeChannelData(self):
        channel_data_offset = 0x800000
        channel_set_list = bytearray(0x200)
        radio_write_data = []
        for i, ch in enumerate(AnyToneMemory.channels):
            if ch.rx_frequency > 0:
                current_byte_idx = int((i - (i % 8))/8)
                channel_set_list[current_byte_idx] = Bit.setBit(channel_set_list[current_byte_idx], i%8, ch.rx_frequency > 0)
                ch_primary_data, ch_secondary_data = ch.encode()

                channel_data_block = int(i / 128)
                primary_data_address = channel_data_offset + ((i - (channel_data_block * 128)) * 0x40) + (channel_data_block * 0x40000)
                secondary_data_address = primary_data_address + 0x2000

                radio_write_data.append((primary_data_address, ch_primary_data))
                radio_write_data.append((secondary_data_address, ch_secondary_data))

                if not self.is_alive:
                    self.finished.emit(AnyToneDevice.STATUS_COM_ERROR)

        self.radio_write_data.append(('Channel Data', radio_write_data))
        self.radio_write_headers.append((0x24c1500, bytes(channel_set_list)))
            
    def writeZoneData(self):
        zone_set_list_addr = 0x24c1300 #0x20
        zone_names_addr = 0x2540000

        zone_name_addr = 0x2540000
        zone_channel_offset = 0x1000000
        zone_a_channel_addr = 0x2500100
        zone_b_channel_addr = 0x2500300
        zone_hide_addr = 0x24c1360

        zone_set_list_data = bytearray(0x20)
        zone_name_data = bytearray([0xff]) * 0x1f40
        zone_a_channel_data = bytearray(0x200)
        zone_b_channel_data = bytearray(0x200)
        # zone_channel_data = bytearray([0xff]) * 0x1000
        zone_hide_data = bytearray(0x20)

        radio_write_data = []
        
        for i, zone in enumerate(AnyToneMemory.zones):
            if len(zone.channels) > 0:
                current_byte_idx = int((i - (i % 8))/8)
                # Zone Set
                zone_set_list_data[current_byte_idx] = Bit.setBit(zone_set_list_data[current_byte_idx], i%8, 1)
                # Zone Name
                radio_write_data.append((zone_names_addr + (i * 0x20), zone.name.encode('utf-8').ljust(0x20, b'\x00')))
                # Zone Channels
                zone_channel_data = bytearray([0xff]) * 0x200
                for ch_idx, ch in enumerate(zone.channels):
                    zone_channel_data[ch_idx * 2: (ch_idx * 2) + 2] = ch.id.to_bytes(2, 'little')

                radio_write_data.append((zone_channel_offset + (i * 0x200), zone_channel_data))
                

                # Zone A Channel
                zone_a_channel_data[i * 2: (i * 2) + 2] = zone.channels.index(zone.a_channel_obj).to_bytes(2, 'little')
                # Zone B Channel
                zone_b_channel_data[i * 2: (i * 2) + 2] = zone.channels.index(zone.b_channel_obj).to_bytes(2, 'little')
            else:
                zone_a_channel_data[i * 2: (i * 2) + 2] = int(0).to_bytes(2, 'little')
                zone_b_channel_data[i * 2: (i * 2) + 2] = int(1).to_bytes(2, 'little')

            # Zone Hide
            zone_hide_data[current_byte_idx] = Bit.setBit(zone_hide_data[current_byte_idx], i%8, zone.hide)

        # radio_write_data.append((zone_channel_offset, zone_channel_data))
        radio_write_data.append((zone_a_channel_addr, zone_a_channel_data))
        radio_write_data.append((zone_b_channel_addr, zone_b_channel_data))
        radio_write_data.append((zone_hide_addr, zone_hide_data))

        self.radio_write_data.append(('Writing Zone Data', radio_write_data))

        self.radio_write_headers.append((zone_set_list_addr, bytes(zone_set_list_data)))

    def writeTalkgroupData(self):
        tg_set_list_addr = 0x2640000
        tg_data_list_addr = 0x2680000
        tg_set_list_data = bytearray([0xff]) * 0x4e3
        tg_data = b''

        for i, tg in enumerate(AnyToneMemory.talkgroups):
            current_byte_idx = int((i - (i % 8))/8)
            tg_set_list_data[current_byte_idx] = Bit.setBit(tg_set_list_data[current_byte_idx], i % 8, tg.tg_dmr_id == 0) # This one you have to inverse if the tg exists
            if tg.tg_dmr_id > 0:
                tg_data += tg.encode()

        # Pad out tg data for alignment
        tg_data = tg_data.ljust((len(tg_data) + 0x10 - (len(tg_data) % 0x10)), b'\x00')
        tg_set_list_data = tg_set_list_data.ljust(0x4f0, b'\x00')

        self.radio_write_headers.append((tg_set_list_addr, tg_set_list_data))
        self.radio_write_data.append(('TalkGroup Data', [(tg_data_list_addr, tg_data)]))

    def writeRadioIdData(self):
        radio_write_data = []
        radio_id_set_list_addr = 0x24c1320 #0x20
        radio_id_set_list = bytearray(0x20)
        radio_id_data_addr = 0x2580000

        for i, rid in enumerate(AnyToneMemory.radioid_list):
            if rid.dmr_id > 0:
                current_byte_idx = int((i - (i % 8))/8)
                radio_id_set_list[current_byte_idx] = Bit.setBit(radio_id_set_list[current_byte_idx], i % 8, True)
                radio_write_data.append((radio_id_data_addr + (i * 0x20), rid.encode()))

        self.radio_write_data.append(('Radio ID Data', radio_write_data))
        self.radio_write_headers.append((radio_id_set_list_addr, bytes(radio_id_set_list)))

    def writeScanListData(self):
        radio_write_data = []
        scan_list_set_list_addr = 0x24c1340 #0x20
        scan_list_data_addr = 0x1080000
        scan_list_set_data = bytearray(0x20)

        for i, sl in enumerate(AnyToneMemory.scanlist):
            if len(sl.channels) > 0:
                current_byte_idx = int((i - (i % 8))/8)
                scan_list_set_data[current_byte_idx] = Bit.setBit(scan_list_set_data[current_byte_idx], i % 8, True)
                radio_write_data.append((scan_list_data_addr + (i * 0x200), sl.encode()))

        self.radio_write_data.append(('Scan List Data', radio_write_data))
        self.radio_write_headers.append((scan_list_set_list_addr, bytes(scan_list_set_data)))

    def writeFMChannelData(self):
        fm_active_scan_addr = 0x2480200
        fm_data = bytearray(0x30)
        fm_freq_data = bytearray([0xff]) * 0x190

        for i, fm in enumerate(AnyToneMemory.fm_channels[:-1]):
            current_byte_idx = int((i - (i % 8))/8)

            # Active Set
            fm_data[0x10 + current_byte_idx] = Bit.setBit(fm_data[0x10 + current_byte_idx], i%8, fm.frequency != 0)

            # Scan/Add Set
            fm_data[0x20 + current_byte_idx] = Bit.setBit(fm_data[0x20 + current_byte_idx], i%8, fm.scan_add and fm.frequency > 0)

            fm_freq_data[i*4: (i*4) + 4] = bytearray(bytes.fromhex(str(fm.frequency).rjust(8,'0')))
            
        for l in range(0, len(fm_freq_data), 16):
            lb = fm_freq_data[l: l + 16]
            if lb == bytes(16):
                fm_freq_data[l: l + 16] = (bytearray([0xff]) * 16)

        # VFO
        vfo = AnyToneMemory.fm_channels[-1]
        fm_data[0:4] = bytearray(bytes.fromhex(str(vfo.frequency).rjust(8,'0')))

        radio_write_data = []
        radio_write_data.append((fm_active_scan_addr, fm_data))
        # radio_write_data.append((0x2480000, fm_freq_data))

        

        self.radio_write_data.append(('FM Data', radio_write_data))

    def writeGpsRoamingData(self):
        radio_write_data = []

        for gps_idx in range(32):
            self.update2.emit(gps_idx, 32, 'Reading GPS Roaming')
            gps_addr = 0x2504000 + ((gps_idx % 16) * 0x20)
            if gps_idx >= 16:
                gps_addr += 0x10
            gps_data = AnyToneMemory.gps_roaming_list[gps_idx].encode()
            radio_write_data.append((gps_addr, gps_data))

        self.radio_write_data.append(('GPS Roaming Data', radio_write_data))
    
    def writeAutoRepeaterFrequencyData(self):
        data = bytearray(0x3f0)
        for i, arf in enumerate(AnyToneMemory.auto_repeater_freq_list):
            addr = i*4
            data[addr:addr+4] = arf.frequency.to_bytes(4, 'little')

        self.radio_write_data.append(('Auto Repeater Frequencies', [(0x24c2000, data)]))
    
    def writeRoamingChannelData(self):
        radio_write_data = []
        header_offset = 0x1042000 #
        data_offset = 0x1040000

        id_set_list = bytearray(0x20)
        for i, rc in enumerate(AnyToneMemory.roaming_channels):
            if rc.rx_frequency > 0:
                current_byte_idx = int((i - (i % 8))/8)
                id_set_list[current_byte_idx] = Bit.setBit(id_set_list[current_byte_idx], i % 8, True)
                radio_write_data.append((data_offset + (i * 0x20), rc.encode()))

        self.radio_write_data.append(('Roaming Channel Data', radio_write_data))
        self.radio_write_headers.append((header_offset, bytes(id_set_list)))

    def writeRoamingZoneData(self):
        radio_write_data = []
        header_offset = 0x1042080
        data_offset = 0x1043000

        id_set_list = bytearray(0x10)

        for i, rz in enumerate(AnyToneMemory.roaming_zones):
            if len(rz.roaming_channels) > 0:
                current_byte_idx = int((i - (i % 8))/8)
                id_set_list[current_byte_idx] = Bit.setBit(id_set_list[current_byte_idx], i % 8, True)
                radio_write_data.append((data_offset + (i * 0x50), rz.encode()))

        
        self.radio_write_data.append(('Roaming Zone Data', radio_write_data))
        self.radio_write_headers.append((header_offset, bytes(id_set_list)))

    def writeSettingsData(self):
        data_0000_addr = 0x2500000 # 0xf0
        data_0600_addr = 0x2500600 # 0x30
        data_1280_addr = 0x2501280 # 0x20
        data_1400_addr = 0x2501400 # 0x100
        data_14_addr = 0x24c1400 #0x20
        data_15_addr = 0x24c1440 #0x30

        data_0000 = bytearray(0xf0)
        data_0600 = bytearray(0x30)
        data_1280 = bytearray(0x20)
        data_1400 = bytearray(0x100)
        data_14 = bytearray(0x20)
        data_15 = bytearray(0x30)

        # Alarm Settings
        data_14[0x0] = AnyToneMemory.alarm_settings.analog_emergency_alarm
        data_14[0x1] = AnyToneMemory.alarm_settings.analog_eni_type
        data_14[0x2] = AnyToneMemory.alarm_settings.analog_emergency_id
        data_14[0x3] = AnyToneMemory.alarm_settings.analog_alarm_time
        data_14[0x4] = AnyToneMemory.alarm_settings.analog_tx_duration
        data_14[0x5] = AnyToneMemory.alarm_settings.analog_rx_duration
        data_14[0x8] = AnyToneMemory.alarm_settings.analog_eni_send
        data_14[0x6] = AnyToneMemory.alarm_settings.analog_emergency_channel
        data_14[0x9] = AnyToneMemory.alarm_settings.analog_emergency_cycle
        data_14[0x12] = AnyToneMemory.alarm_settings.work_mode_voice_switch
        data_14[0x13] = AnyToneMemory.alarm_settings.work_mode_area_switch
        data_14[0x14] = AnyToneMemory.alarm_settings.work_mode_mic_switch
        data_14[0xa] = AnyToneMemory.alarm_settings.digital_emergency_alarm
        data_14[0xb] = AnyToneMemory.alarm_settings.digital_alarm_time
        data_14[0xc] = AnyToneMemory.alarm_settings.digital_tx_duration
        data_14[0xd] = AnyToneMemory.alarm_settings.digital_rx_duration
        data_14[0x10] = AnyToneMemory.alarm_settings.digital_eni_send
        data_14[0xe] = AnyToneMemory.alarm_settings.digital_emergency_channel
        data_14[0x11] = AnyToneMemory.alarm_settings.digital_emergency_cycle
        data_15[0x23:0x27] = bytearray(bytes.fromhex(str(AnyToneMemory.alarm_settings.digital_tg_dmr_id).rjust(4,'0')))
        data_15[0x0] = AnyToneMemory.alarm_settings.digital_call_type
        data_14[0x15] = AnyToneMemory.alarm_settings.receive_alarm
        data_0000[0x24] = AnyToneMemory.alarm_settings.man_down
        data_0000[0x4f] = AnyToneMemory.alarm_settings.man_down_delay

        # Optional Settings
        # Power-on
        data_0000[0x6] = AnyToneMemory.optional_settings.poweron_interface
        data_0600[0x0:0xe] = AnyToneMemory.optional_settings.poweron_display_1
        data_0600[0x10:0x1e] = AnyToneMemory.optional_settings.poweron_display_2
        data_0000[0x7] = AnyToneMemory.optional_settings.poweron_password
        data_0600[0x20:0x28] = AnyToneMemory.optional_settings.poweron_password_char.encode('utf-8').ljust(8, b'\x00')
        data_0000[0xd7] = AnyToneMemory.optional_settings.default_startup_channel
        data_0000[0xd8] = AnyToneMemory.optional_settings.startup_zone_a
        data_0000[0xda] = AnyToneMemory.optional_settings.startup_channel_a
        data_0000[0xd9] = AnyToneMemory.optional_settings.startup_zone_b
        data_0000[0xdb] = AnyToneMemory.optional_settings.startup_channel_b
        data_0000[0xeb] = AnyToneMemory.optional_settings.startup_gps_test
        data_0000[0xec] = AnyToneMemory.optional_settings.startup_reset

        # Power Save
        data_0000[0x3] = AnyToneMemory.optional_settings.auto_shutdown
        data_0000[0xb] = AnyToneMemory.optional_settings.power_save
        data_1400[0x3f] = AnyToneMemory.optional_settings.auto_shutdown_type 

        # Display
        data_0000[0x26] = AnyToneMemory.optional_settings.brightness
        data_0000[0x27] = AnyToneMemory.optional_settings.auto_backlight_duration
        data_0000[0xe1] = AnyToneMemory.optional_settings.backlight_tx_delay
        data_0000[0x37] = AnyToneMemory.optional_settings.menu_exit_time
        data_0000[0x51] = AnyToneMemory.optional_settings.time_display
        data_0000[0x4d] = AnyToneMemory.optional_settings.last_caller
        data_0000[0xaf] = AnyToneMemory.optional_settings.call_display_mode
        data_0000[0xbc] = AnyToneMemory.optional_settings.callsign_display_color
        data_0000[0x3a] = AnyToneMemory.optional_settings.call_end_prompt_box
        data_0000[0xb8] = AnyToneMemory.optional_settings.display_channel_number
        data_0000[0xb9] = AnyToneMemory.optional_settings.display_current_contact
        data_0000[0xc0] = AnyToneMemory.optional_settings.standby_char_color
        data_0000[0xc1] = AnyToneMemory.optional_settings.standby_bk_picture
        data_0000[0xc2] = AnyToneMemory.optional_settings.show_last_call_on_launch
        data_0000[0xe2] = AnyToneMemory.optional_settings.separate_display
        data_0000[0xe3] = AnyToneMemory.optional_settings.ch_switching_keeps_caller
        data_0000[0xe6] = AnyToneMemory.optional_settings.backlight_rx_delay
        data_0000[0xe4] = AnyToneMemory.optional_settings.channel_name_color_a
        data_1400[0x39] = AnyToneMemory.optional_settings.channel_name_color_b
        data_1400[0x3d] = AnyToneMemory.optional_settings.zone_name_color_a
        data_1400[0x3e] = AnyToneMemory.optional_settings.zone_name_color_b
        data_1400[0x40] = Bit.setBit(data_1400[0x40], 0, AnyToneMemory.optional_settings.display_channel_type)
        data_1400[0x40] = Bit.setBit(data_1400[0x40], 1, AnyToneMemory.optional_settings.display_time_slot)
        data_1400[0x40] = Bit.setBit(data_1400[0x40], 2, AnyToneMemory.optional_settings.display_color_code)
        data_1400[0x42] = AnyToneMemory.optional_settings.date_display_format
        data_0000[0x47] = AnyToneMemory.optional_settings.volume_bar

        # Work Mode
        data_0000[0x01] = AnyToneMemory.optional_settings.display_mode
        data_0000[0x15] = AnyToneMemory.optional_settings.vf_mr_a
        data_0000[0x16] = AnyToneMemory.optional_settings.vf_mr_b
        data_0000[0x1f] = AnyToneMemory.optional_settings.mem_zone_a
        data_0000[0x20] = AnyToneMemory.optional_settings.mem_zone_b
        data_0000[0x2c] = AnyToneMemory.optional_settings.main_channel_set
        data_0000[0x2d] = AnyToneMemory.optional_settings.sub_channel_mode
        data_0000[0x34] = AnyToneMemory.optional_settings.working_mode

        # Vox/BT
        data_0000[0x0c] = AnyToneMemory.optional_settings.vox_level
        data_0000[0x0d] = AnyToneMemory.optional_settings.vox_delay
        data_0000[0x33] = AnyToneMemory.optional_settings.vox_detection
        data_0000[0xb1] = AnyToneMemory.optional_settings.bt_on_off
        data_0000[0xb2] = AnyToneMemory.optional_settings.bt_int_mic
        data_0000[0xb3] = AnyToneMemory.optional_settings.bt_int_spk
        data_0000[0xb6] = AnyToneMemory.optional_settings.bt_mic_gain
        data_0000[0xb7] = AnyToneMemory.optional_settings.bt_spk_gain
        data_0000[0xed] = AnyToneMemory.optional_settings.bt_hold_time
        data_0000[0xee] = AnyToneMemory.optional_settings.bt_rx_delay
        data_1400[0x21] = AnyToneMemory.optional_settings.bt_ptt_hold
        data_1400[0x34] = AnyToneMemory.optional_settings.bt_ptt_sleep_time

        # STE
        data_0000[0x17] = AnyToneMemory.optional_settings.ste_type_of_ctcss
        data_0000[0x18] = AnyToneMemory.optional_settings.ste_when_no_signal
        data_1400[0x36] = AnyToneMemory.optional_settings.ste_time

        # FM
        data_0000[0x1e] = AnyToneMemory.optional_settings.fm_vfo_mem
        data_0000[0x1d] = AnyToneMemory.optional_settings.fm_work_channel
        data_0000[0x2b] = AnyToneMemory.optional_settings.fm_monitor
        # Key Function
        data_0000[0x02] = AnyToneMemory.optional_settings.key_lock
        data_0000[0x10] = AnyToneMemory.optional_settings.pf1_short_key
        data_0000[0x11] = AnyToneMemory.optional_settings.pf2_short_key
        data_0000[0x12] = AnyToneMemory.optional_settings.pf3_short_key
        data_0000[0x13] = AnyToneMemory.optional_settings.p1_short_key
        data_0000[0x14] = AnyToneMemory.optional_settings.p2_short_key
        data_0000[0x41] = AnyToneMemory.optional_settings.pf1_long_key
        data_0000[0x42] = AnyToneMemory.optional_settings.pf2_long_key
        data_0000[0x43] = AnyToneMemory.optional_settings.pf3_long_key
        data_0000[0x44] = AnyToneMemory.optional_settings.p1_long_key
        data_0000[0x45] = AnyToneMemory.optional_settings.p2_long_key
        data_0000[0x46] = AnyToneMemory.optional_settings.long_key_time
        data_0000[0xbe] = Bit.setBit(data_0000[0xbe], 0, AnyToneMemory.optional_settings.knob_lock)
        data_0000[0xbe] = Bit.setBit(data_0000[0xbe], 1, AnyToneMemory.optional_settings.keyboard_lock)
        data_0000[0xbe] = Bit.setBit(data_0000[0xbe], 3, AnyToneMemory.optional_settings.side_key_lock)
        data_0000[0xbe] = Bit.setBit(data_0000[0xbe], 4, AnyToneMemory.optional_settings.forced_key_lock)

        # Other
        if AnyToneMemory.optional_settings.priority_zone_a == 0:
            AnyToneMemory.optional_settings.priority_zone_a = 0xff
        else:
            AnyToneMemory.optional_settings.priority_zone_a -= 1

        if AnyToneMemory.optional_settings.priority_zone_b == 0:
            AnyToneMemory.optional_settings.priority_zone_b = 0xff
        else:
            AnyToneMemory.optional_settings.priority_zone_b -= 1
        data_0000[0xd5] = AnyToneMemory.optional_settings.address_book_sent_with_code
        data_0000[0x04] = AnyToneMemory.optional_settings.tot
        data_0000[0x05] = AnyToneMemory.optional_settings.language
        data_0000[0x08] = AnyToneMemory.optional_settings.frequency_step
        data_0000[0x09] = AnyToneMemory.optional_settings.sql_level_a
        data_0000[0x0a] = AnyToneMemory.optional_settings.sql_level_b
        data_0000[0x2e] = AnyToneMemory.optional_settings.tbst
        data_0000[0x50] = AnyToneMemory.optional_settings.analog_call_hold_time
        data_0000[0x6e] = AnyToneMemory.optional_settings.call_channel_maintained
        data_0000[0x6f] = AnyToneMemory.optional_settings.priority_zone_a
        data_0000[0x70] = AnyToneMemory.optional_settings.priority_zone_b
        data_0000[0xe9] = AnyToneMemory.optional_settings.mute_timing
        data_1400[0x3a] = AnyToneMemory.optional_settings.encryption_type
        data_1400[0x3b] = AnyToneMemory.optional_settings.tot_predict
        data_1400[0x3c] = AnyToneMemory.optional_settings.tx_power_agc

        # Digital Func
        data_0000[0x19] = AnyToneMemory.optional_settings.group_call_hold_time
        data_0000[0x1a] = AnyToneMemory.optional_settings.private_call_hold_time
        data_1400[0x37] = AnyToneMemory.optional_settings.manual_dial_group_call_hold_time
        data_1400[0x38] = AnyToneMemory.optional_settings.manual_dial_private_call_hold_time
        data_1400[0x6e] = AnyToneMemory.optional_settings.voice_header_repetitions
        data_0000[0x1c] = AnyToneMemory.optional_settings.tx_preamble_duration
        data_0000[0x38] = AnyToneMemory.optional_settings.filter_own_id
        data_0000[0x3c] = AnyToneMemory.optional_settings.digital_remote_kill
        data_0000[0x49] = AnyToneMemory.optional_settings.digital_monitor
        data_0000[0x4a] = AnyToneMemory.optional_settings.digital_monitor_cc
        data_0000[0x4b] = AnyToneMemory.optional_settings.digital_monitor_id
        data_0000[0x4c] = AnyToneMemory.optional_settings.monitor_slot_hold
        data_0000[0x3e] = AnyToneMemory.optional_settings.remote_monitor
        data_0000[0xc3] = AnyToneMemory.optional_settings.sms_format

        # Alert Tone
        data_0000[0x29] = AnyToneMemory.optional_settings.sms_alert
        data_0000[0x2f] = AnyToneMemory.optional_settings.call_alert
        data_0000[0x32] = AnyToneMemory.optional_settings.digi_call_reset_tone
        data_0000[0x31] = AnyToneMemory.optional_settings.talk_permit
        data_0000[0x00] = AnyToneMemory.optional_settings.key_tone
        data_0000[0x36] = AnyToneMemory.optional_settings.digi_idle_channel_tone
        data_0000[0x39] = AnyToneMemory.optional_settings.startup_sound
        data_0000[0xbb] = AnyToneMemory.optional_settings.tone_key_sound_adjustable
        data_1400[0x41] = AnyToneMemory.optional_settings.analog_idle_channel_tone
        data_0000[0xb4] = AnyToneMemory.optional_settings.plugin_recording_tone
        data_0000[0x72:0x74] = AnyToneMemory.optional_settings.call_permit_first_tone_freq.to_bytes(2, 'little')
        data_0000[0x7c:0x7e] = AnyToneMemory.optional_settings.call_permit_first_tone_period.to_bytes(2, 'little')
        data_0000[0x74:0x76] = AnyToneMemory.optional_settings.call_permit_second_tone_freq.to_bytes(2, 'little')
        data_0000[0x7e:0x80] = AnyToneMemory.optional_settings.call_permit_second_tone_period.to_bytes(2, 'little')
        data_0000[0x76:0x78] = AnyToneMemory.optional_settings.call_permit_third_tone_freq.to_bytes(2, 'little')
        data_0000[0x80:0x82] = AnyToneMemory.optional_settings.call_permit_third_tone_period.to_bytes(2, 'little')
        data_0000[0x78:0x7a] = AnyToneMemory.optional_settings.call_permit_fourth_tone_freq.to_bytes(2, 'little')
        data_0000[0x82:0x84] = AnyToneMemory.optional_settings.call_permit_fourth_tone_period.to_bytes(2, 'little')
        data_0000[0x7a:0x7c] = AnyToneMemory.optional_settings.call_permit_fifth_tone_freq.to_bytes(2, 'little')
        data_0000[0x84:0x86] = AnyToneMemory.optional_settings.call_permit_fifth_tone_period.to_bytes(2, 'little')
        data_0000[0x86:0x88] = AnyToneMemory.optional_settings.idle_channel_first_tone_freq.to_bytes(2, 'little')
        data_0000[0x90:0x92] = AnyToneMemory.optional_settings.idle_channel_first_tone_period.to_bytes(2, 'little')
        data_0000[0x88:0x8a] = AnyToneMemory.optional_settings.idle_channel_second_tone_freq.to_bytes(2, 'little')
        data_0000[0x92:0x94] = AnyToneMemory.optional_settings.idle_channel_second_tone_period.to_bytes(2, 'little')
        data_0000[0x8a:0x8c] = AnyToneMemory.optional_settings.idle_channel_third_tone_freq.to_bytes(2, 'little')
        data_0000[0x94:0x96] = AnyToneMemory.optional_settings.idle_channel_third_tone_period.to_bytes(2, 'little')
        data_0000[0x8c:0x8e] = AnyToneMemory.optional_settings.idle_channel_fourth_tone_freq.to_bytes(2, 'little')
        data_0000[0x96:0x98] = AnyToneMemory.optional_settings.idle_channel_fourth_tone_period.to_bytes(2, 'little')
        data_0000[0x8e:0x90] = AnyToneMemory.optional_settings.idle_channel_fifth_tone_freq.to_bytes(2, 'little')
        data_0000[0x98:0x9a] = AnyToneMemory.optional_settings.idle_channel_fifth_tone_period.to_bytes(2, 'little')
        data_0000[0x9a:0x9c] = AnyToneMemory.optional_settings.call_reset_first_tone_freq.to_bytes(2, 'little')
        data_0000[0xa4:0xa6] = AnyToneMemory.optional_settings.call_reset_first_tone_period.to_bytes(2, 'little')
        data_0000[0x9c:0x9e] = AnyToneMemory.optional_settings.call_reset_second_tone_freq.to_bytes(2, 'little')
        data_0000[0xa6:0xa8] = AnyToneMemory.optional_settings.call_reset_second_tone_period.to_bytes(2, 'little')
        data_0000[0x9e:0xa0] = AnyToneMemory.optional_settings.call_reset_third_tone_freq.to_bytes(2, 'little')
        data_0000[0xa8:0xaa] = AnyToneMemory.optional_settings.call_reset_third_tone_period.to_bytes(2, 'little')
        data_0000[0xa0:0xa2] = AnyToneMemory.optional_settings.call_reset_fourth_tone_freq.to_bytes(2, 'little')
        data_0000[0xaa:0xac] = AnyToneMemory.optional_settings.call_reset_fourth_tone_period.to_bytes(2, 'little')
        data_0000[0xa2:0xa4] = AnyToneMemory.optional_settings.call_reset_fifth_tone_freq.to_bytes(2, 'little')
        data_0000[0xac:0xae] = AnyToneMemory.optional_settings.call_reset_fifth_tone_period.to_bytes(2, 'little')

        # Alert Tone 1
        data_1400[0x46:0x48] = AnyToneMemory.optional_settings.call_end_first_tone_freq.to_bytes(2, 'little')
        data_1400[0x50:0x52] = AnyToneMemory.optional_settings.call_end_first_tone_period.to_bytes(2, 'little')
        data_1400[0x48:0x4a] = AnyToneMemory.optional_settings.call_end_second_tone_freq.to_bytes(2, 'little')
        data_1400[0x52:0x54] = AnyToneMemory.optional_settings.call_end_second_tone_period.to_bytes(2, 'little')
        data_1400[0x4a:0x4c] = AnyToneMemory.optional_settings.call_end_third_tone_freq.to_bytes(2, 'little')
        data_1400[0x54:0x56] = AnyToneMemory.optional_settings.call_end_third_tone_period.to_bytes(2, 'little')
        data_1400[0x4c:0x4e] = AnyToneMemory.optional_settings.call_end_fourth_tone_freq.to_bytes(2, 'little')
        data_1400[0x56:0x58] = AnyToneMemory.optional_settings.call_end_fourth_tone_period.to_bytes(2, 'little')
        data_1400[0x4e:0x50] = AnyToneMemory.optional_settings.call_end_fifth_tone_freq.to_bytes(2, 'little')
        data_1400[0x58:0x5a] = AnyToneMemory.optional_settings.call_end_fifth_tone_period.to_bytes(2, 'little')
        data_1400[0x5a:0x5c] = AnyToneMemory.optional_settings.call_all_first_tone_freq.to_bytes(2, 'little')
        data_1400[0x64:0x66] = AnyToneMemory.optional_settings.call_all_first_tone_period.to_bytes(2, 'little')
        data_1400[0x5c:0x5e] = AnyToneMemory.optional_settings.call_all_second_tone_freq.to_bytes(2, 'little')
        data_1400[0x66:0x68] = AnyToneMemory.optional_settings.call_all_second_tone_period.to_bytes(2, 'little')
        data_1400[0x5e:0x60] = AnyToneMemory.optional_settings.call_all_third_tone_freq.to_bytes(2, 'little')
        data_1400[0x68:0x6a] = AnyToneMemory.optional_settings.call_all_third_tone_period.to_bytes(2, 'little')
        data_1400[0x60:0x62] = AnyToneMemory.optional_settings.call_all_fourth_tone_freq.to_bytes(2, 'little')
        data_1400[0x6a:0x6c] = AnyToneMemory.optional_settings.call_all_fourth_tone_period.to_bytes(2, 'little')
        data_1400[0x62:0x64] = AnyToneMemory.optional_settings.call_all_fifth_tone_freq.to_bytes(2, 'little')
        data_1400[0x6c:0x6e] = AnyToneMemory.optional_settings.call_all_fifth_tone_period.to_bytes(2, 'little')

        # GPS/Ranging
        data_0000[0x28] = AnyToneMemory.optional_settings.gps_power
        data_0000[0x3f] = AnyToneMemory.optional_settings.gps_positioning
        data_0000[0x30] = AnyToneMemory.optional_settings.time_zone
        data_0000[0xb5] = AnyToneMemory.optional_settings.ranging_interval
        data_0000[0xbd] = AnyToneMemory.optional_settings.distance_unit
        data_0000[0x53] = AnyToneMemory.optional_settings.gps_template_information
        data_1280[0x0:0x20] = AnyToneMemory.optional_settings.gps_information_char.encode('utf-8').ljust(0x20, b'\x00')
        data_1400[0x35] = AnyToneMemory.optional_settings.gps_mode
        # AnyToneMemory.optional_settings.gps_roaming = int(data_0000[0x])

        # VFO Scan
        data_0000[0x0e] = AnyToneMemory.optional_settings.vfo_scan_type
        data_0000[0x58:0x5c] = AnyToneMemory.optional_settings.vfo_scan_start_freq_uhf.to_bytes(4, 'little')
        data_0000[0x5c:0x60] = AnyToneMemory.optional_settings.vfo_scan_end_freq_uhf.to_bytes(4, 'little')
        data_0000[0x60:0x64] = AnyToneMemory.optional_settings.vfo_scan_start_freq_vhf.to_bytes(4, 'little')
        data_0000[0x64:0x68] = AnyToneMemory.optional_settings.vfo_scan_end_freq_vhf.to_bytes(4, 'little')

        # Auto Repeater
        data_0000[0x48] = AnyToneMemory.optional_settings.auto_repeater_a
        data_0000[0xd4] = AnyToneMemory.optional_settings.auto_repeater_b
        data_0000[0x68] = AnyToneMemory.optional_settings.auto_repeater_1_uhf
        data_0000[0x69] = AnyToneMemory.optional_settings.auto_repeater_1_vhf
        data_1400[0x22] = AnyToneMemory.optional_settings.auto_repeater_2_uhf
        data_1400[0x23] = AnyToneMemory.optional_settings.auto_repeater_2_vhf
        data_0000[0xdd] = AnyToneMemory.optional_settings.repeater_check
        data_0000[0xde] = AnyToneMemory.optional_settings.repeater_check_interval
        data_0000[0xdf] = AnyToneMemory.optional_settings.repeater_check_reconnections
        data_0000[0xe5] = AnyToneMemory.optional_settings.repeater_out_of_range_notify
        data_0000[0xea] = AnyToneMemory.optional_settings.out_of_range_notify
        data_0000[0xe7] = AnyToneMemory.optional_settings.auto_roaming
        data_0000[0xe0] = AnyToneMemory.optional_settings.auto_roaming_start_condition
        data_0000[0xba] = AnyToneMemory.optional_settings.auto_roaming_fixed_time
        data_0000[0xbf] = AnyToneMemory.optional_settings.roaming_effect_wait_time
        data_0000[0xd5] = AnyToneMemory.optional_settings.roaming_zone
        data_0000[0xc4:0xc8] = AnyToneMemory.optional_settings.auto_repeater_1_min_freq_vhf.to_bytes(4, 'little')
        data_0000[0xc8:0xcc] = AnyToneMemory.optional_settings.auto_repeater_1_max_freq_vhf.to_bytes(4, 'little')
        data_0000[0xcc:0xd0] = AnyToneMemory.optional_settings.auto_repeater_1_min_freq_uhf.to_bytes(4, 'little')
        data_0000[0xd0:0xd4] = AnyToneMemory.optional_settings.auto_repeater_1_max_freq_uhf.to_bytes(4, 'little')
        data_1400[0x24:0x28] = AnyToneMemory.optional_settings.auto_repeater_2_min_freq_vhf.to_bytes(4, 'little')
        data_1400[0x28:0x2c] = AnyToneMemory.optional_settings.auto_repeater_2_max_freq_vhf.to_bytes(4, 'little')
        data_1400[0x2c:0x30] = AnyToneMemory.optional_settings.auto_repeater_2_min_freq_uhf.to_bytes(4, 'little')
        data_1400[0x30:0x34] = AnyToneMemory.optional_settings.auto_repeater_2_max_freq_uhf.to_bytes(4, 'little')

        # Record
        AnyToneMemory.optional_settings.record_function = int(data_0000[0x22])

        # Volume/Audio
        data_0000[0x3b] = AnyToneMemory.optional_settings.max_volume
        data_0000[0x52] = AnyToneMemory.optional_settings.max_headphone_volume
        data_0000[0x0f] = AnyToneMemory.optional_settings.digi_mic_gain
        data_0000[0x57] = AnyToneMemory.optional_settings.enhanced_sound_quality
        data_1400[0x43] = AnyToneMemory.optional_settings.analog_mic_gain

        # Unknown
        data_1400[0x6f] = AnyToneMemory.optional_settings.data_250146f

        radio_write_data = []
        radio_write_data.append((data_0000_addr, data_0000))
        radio_write_data.append((data_0600_addr, data_0600))
        radio_write_data.append((data_1280_addr, data_1280))
        radio_write_data.append((data_1400_addr, data_1400))
        radio_write_data.append((data_14_addr, data_14))
        radio_write_data.append((data_15_addr, data_15))

        self.radio_write_data.append(('Writing Settings', radio_write_data))

    def writeMasterRadioIdData(self):
        data = AnyToneMemory.master_radioid.encode()
        self.radio_write_data.append(('Master ID Data', [(0x2582000, data)]))


    # Read Memory Functions
    def readBootImage(self):
        self.image_data = b''
        for i in range(0, 0xa000, 0x10):
            self.image_data += self.readMemory(0x2ac0000 + i, 0x10)
            self.update1.emit(i, 0, '')

    def readBk1Image(self):
        self.image_data = b''
        for i in range(0, 0xa000, 0x10):
            self.image_data += self.readMemory(0x2b00000 + i, 0x10)
            self.update1.emit(i, 0, '')

    def readBk2Image(self):
        self.image_data = b''
        for i in range(0, 0xa000, 0x10):
            self.image_data += self.readMemory(0x2b80000 + i, 0x10)
            self.update1.emit(i, 0, '')

    def readMemory(self, start_address, read_len):
        data = b''
        for addr in range(start_address, start_address + read_len, 0x10):
            data += self.readMemoryAddress(addr, 0x10)[0]

        return data

    def readRadioData(self):
        
        local_info = self.readDeviceInfo()
        if local_info[0] != 'ID878UV2' or local_info[1] != 'V101': # TODO: Update this when adding new models
            self.finished.emit(AnyToneDevice.STATUS_DEVICE_MISMATCH)
            return

        if self.read_write_options == AnyToneDevice.RADIO_DATA or self.read_write_options == AnyToneDevice.RADIO_DATA_CONTACTS:
            self.readOtherData()
        elif self.read_write_options == AnyToneDevice.DIGITAL_CONTACTS:
            self.readDigitalContacts()
        elif self.read_write_options == AnyToneDevice.BOOT_IMAGE:
            self.readBootImage()
        elif self.read_write_options == AnyToneDevice.BK1_IMAGE:
            self.readBk1Image()
        elif self.read_write_options == AnyToneDevice.BK2_IMAGE:
            self.readBk2Image()

    # Digital Contact
    def readDigitalContacts(self):
        contact_count = int.from_bytes(self.readMemory(0x4840000, 16)[0:4], 'little')

        contact_data = bytearray()
        offset = 0
        for i in range(contact_count):
            self.update2.emit(i, contact_count, 'Reading Contacts')

            if len(contact_data) - offset < 0x80:
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
        roaming_channel_set_data = self.readMemory(0x1042000, 0x20) # Roaming Channel Set List = 1 |
        roaming_zone_set_data = self.readMemory(0x1042080, 0x10) # Roaming Zone Set List = 1 |
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
        data_14 = self.readMemory(0x24c1400, 0x20) # Alarm Settings 
        data_15 = self.readMemory(0x24c1440, 0x30) # Alarm Settings 
        channel_set_data = self.readMemory(0x24c1500, 0x200) # Channels Exist = 1
        # data_16 = self.readMemory(0x24c1700, 0x40) #
        # data_17 = self.readMemory(0x24c1800, 0x500) # 
        auto_repeater_offset_data = self.readMemory(0x24c2000, 0x3f0) # Auto Repeater Offset Frequencies
        # data_19 = self.readMemory(0x24c2600, 0x10) # 
        # data_20 = self.readMemory(0x24c4000, 0x4000) # 
        optional_settings_data_0000 = self.readMemory(0x2500000, 0xf0) # Optional Settings / Alarm Settings
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

        self.readAlarmSettings(optional_settings_data_0000, data_14, data_15)
        
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

    def readAlarmSettings(self, data_0000: bytes, data_1400: bytes, data_1440: bytes):
        AnyToneMemory.alarm_settings.decode(data_0000, data_1400, data_1440)


# # Use this virtual dev to save the output from the original CPS using com0com on windows.
# dev = AnyToneDevice()
# Preload with previously saved bin
# with open('saved.bin', 'rb') as f:
#     dev.bin_data = bytearray(f.read())
# dev.startSerial("COM7")
# # Write BIN Data once CPS is completed the write
# with open('bin-dump3.bin', 'wb') as f:
#     f.write(dev.bin_data)
class AnyToneVirtualDevice(AnyToneDevice):
    verbose = False
    serial_port = None
    save_write_data = True

    # Data BIN Size
    # Other Data        0x48001d0
    # Digital Contacts  0x
    bin_data = bytearray([0xff] * 0x48001D0) # This is big enough for main data; Needs to be resized when writing or reading contact data
    is_open = True

    # Optional debugging outputs
    address_blocks = '' # The address blocks and size that are being written
    command_list = []   # List of all data being sent via serial port (Command, address, data length, [data, checksum], EOL)
    max_address = 0

    last_block_start = 0
    last_addr = 0

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

    def writeMemoryAddress(self, address, data: bytes):
        if len(data) % 16 != 0:
            print('Error: Memory Alignment', hex(address), hex(len(data)))

        if type(self.bin_data) == bytes:
            self.bin_data = bytearray(self.bin_data)
        self.bin_data[address: address + len(data)] = bytearray(data)

    # This is for use outside of the GUI to read serial data. 
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

                if self.save_write_data:
                    for i, b in enumerate(bytearray(rdata)):
                        self.bin_data[address + i] = b

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
                # print("MAX Address:", hex(self.max_address + 0x10))

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
        return bytes(0x100)
    
    def readDeviceInfo(self):
        return ('ID878UV2', 'V101')
    
class AnyToneSerial(AnyToneDevice):
    serial_port: QSerialPort = None
    device_info = (b'', b'')

    max_bytes_per_read_message = 16 # Anytone CPS uses 16, up to 255 possible
    max_bytes_per_write_message = 16 # Anytone CPS uses 16, more possible?

    # Serial Functions
    def connect(self, portname: str, baud=921600):
        self.serial_port = QSerialPort()
        self.serial_port.setPortName(portname)
        self.serial_port.setBaudRate(baud)

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
    
    # Radio Functions
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

        resp = self.read_blocking()
        
        if resp != b'\x06':
            print ('ERR: Unexpected response from device (' + str(resp) + ')' )
            exit()

    def endUpdateMode(self):

        # leave pc mode
        self.serial_port.write(b'\x18')

        resp = self.read_blocking()

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
    
    def readMemoryAddress(self, address, num_bytes_left):
        if num_bytes_left % 16 != 0:
            print('Error: Memory Alignment')
        if not self.is_alive:
            return [b'', 0]
        
        resp = bytearray()
            
        while num_bytes_left > 0:
        
            num_bytes = min(num_bytes_left, self.max_bytes_per_read_message)
        
            readcmd = bytearray()
            readcmd.append( ord('R') )
            readcmd.append( (address & 0xff000000) >> 24 )
            readcmd.append( (address & 0x00ff0000) >> 16 )
            readcmd.append( (address & 0x0000ff00) >> 8 )
            readcmd.append( (address & 0x000000ff) )
            readcmd.append( num_bytes )
        
            self.serial_port.write(readcmd)

            message = self.read_blocking()
            if len(message) < 24:
                self.is_alive = False
                return [b'', 0]
            
            checksum = sum(message[1:-2]) & 0xff
            
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
            return

        num_bytes_left = len(data)
        dataptr = 0
            
        while num_bytes_left > 0:
        
            num_bytes = min(num_bytes_left, self.max_bytes_per_write_message)
            
            # while num_bytes_left < self.max_bytes_per_write_message:
            #     # pad with zeros to reach at least 16 bytes per message
            #     data.append(0)
            #     num_bytes_left += 1
            #     num_bytes += 1
                
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

            self.serial_port.write(writecmd)
        
            # read answer
            answ = self.read_blocking()
            
            if answ[0] == 0x06:
                # ack received, ok
                num_bytes_left -= num_bytes
                dataptr += num_bytes
                address += num_bytes
            else:
                # no response. write again
                print('WARN: No response on write request. Retransmitting at ' + str(address) )
    
    # Unused Functions; May implement later
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
    is_write = False
    image_data = b''

    def setComport(self, comport: str):
        self.comport = comport

    def setVirtualFile(self, bin_file: str):
        self.bin_file = bin_file

    def setReadWriteOptions(self, read_write_options: int):
        self.read_write_options = read_write_options

    def run(self):
        if self.comport != None:
            self.radio_device = AnyToneSerial()
            self.radio_device.image_data = self.image_data
            self.radio_device.read_write_options = self.read_write_options
            self.radio_device.update1.connect(self.signals.update1)
            self.radio_device.update2.connect(self.signals.update2)
            self.radio_device.finished.connect(self.signals.finished)

            while(not self.radio_device.is_alive and self.connection_attempt < 5):
                self.connection_attempt += 1
                if self.radio_device.connect(self.comport):
                    if self.is_write:
                        self.radio_device.writeRadioData()
                    else:
                        self.radio_device.readRadioData()
                    if self.radio_device.is_alive:
                        self.radio_device.endProgMode()
                if not self.radio_device.is_alive:
                    time.sleep(1)
            
            self.radio_device.closeDevice()

            if self.radio_device.is_alive:
                self.signals.finished.emit(AnyToneDevice.STATUS_SUCCESS)
            else:
                self.signals.finished.emit(AnyToneDevice.STATUS_COM_ERROR)

        elif self.bin_file != None:
            self.radio_device = AnyToneVirtualDevice()
            self.radio_device.image_data = self.image_data
            self.radio_device.read_write_options = self.read_write_options
            self.radio_device.update1.connect(self.signals.update1)
            self.radio_device.update2.connect(self.signals.update2)
            self.radio_device.finished.connect(self.signals.finished)
            self.radio_device.loadBin(self.bin_file)
            if self.is_write:
                self.radio_device.writeRadioData()
                with open(os.path.join('CPS Debug', 'saved.bin'), 'wb') as f:
                    f.write(self.radio_device.bin_data)
            else:
                self.radio_device.readRadioData()
            self.signals.finished.emit(AnyToneDevice.STATUS_SUCCESS)

        self.radio_device.update1.disconnect()
        self.radio_device.update2.disconnect()
        self.radio_device.finished.disconnect()
