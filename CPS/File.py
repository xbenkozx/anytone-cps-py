import pandas as pd
from decimal import Decimal
from PySide6.QtCore import QRunnable
from CPS.AnytoneMemory import *
class CSVImport(MemoryController):
    def __init__(self):
        super().__init__()
    def importRadioIdData(self, filepath):
        self.update2.emit(0, 1, "Importing Radio IDs")
        df = pd.read_csv(filepath, keep_default_na=False, na_values=[])
        row_count = len(df)
        AnyToneMemory.initRadioIdList()
        for index, row in df.iterrows():
            self.update2.emit(index, row_count, None)
            rid = AnyToneMemory.radioid_list[int(row['No.']) - 1]
            rid.dmr_id = int(row['Radio ID'])
            rid.name = row['Name']
    def importChannelData(self, filepath):
        self.update2.emit(0, 1, "Importing Channels")
        df = pd.read_csv(filepath, dtype={'Receive Frequency': str, 'Transmit Frequency':str}, keep_default_na=False, na_values=[])
        row_count = len(df)
        AnyToneMemory.initChannels()
        for index, row in df.iterrows():
            self.update2.emit(index, row_count, None)
            ch = self.memory.channels[int(row['No.']) - 1]
            ch.name = row['Channel Name']
            ch.rx_frequency = int(Decimal(row['Receive Frequency']) * 100000)
            tx_offset = ch.rx_frequency - int(Decimal(row['Transmit Frequency']) * 100000)
            if tx_offset == 0:
                ch.offset_direction = 0
            elif tx_offset > 0:
                ch.offset_direction = 2
            else:
                ch.offset_direction = 1
                tx_offset = tx_offset * -1
            ch.offset = tx_offset
            ch.channel_type = Constants.ChannelType.index(row['Channel Type'])
            ch.tx_power = Constants.TxPower.index(row['Transmit Power'])
            ch.band_width = Constants.BandWidth.index(row['Band Width'])
            ctcss_decode = row['CTCSS/DCS Decode']
            ctcss_encode = row['CTCSS/DCS Encode']
            if ctcss_decode == 'Off':
                ch.ctcss_dcs_decode = 0
            else:
                try:
                    ch.ctcss_decode_tone = Constants.CTCSSCode.index(ctcss_decode)
                    ch.ctcss_dcs_decode = 1
                except:
                    pass
                try:
                    ch.dcs_decode_tone = Constants.DCSCode.index(ctcss_decode)
                    ch.ctcss_dcs_decode = 2
                except:
                    pass
            if ctcss_encode == 'Off':
                ch.ctcss_dcs_encode = 0
            else:
                try:
                    ch.ctcss_encode_tone = Constants.CTCSSCode.index(ctcss_encode)
                    ch.ctcss_dcs_encode = 1
                except:
                    pass
                try:
                    ch.dcs_encode_tone = Constants.DCSCode.index(ctcss_encode)
                    ch.ctcss_dcs_encode = 2
                except:
                    pass
            ch.temp_talkgroup = (row['Contact'], int(row['Contact TG/DMR ID']))
            ch.temp_radio_id = row['Radio ID']
            ch.busy_lock = ['Off', 'Always'].index(row['Busy Lock/TX Permit'])
            ch.squelch_mode = ['Carrier', 'CTCSS/DCS'].index(row['Squelch Mode'])
            ch.optional_signal = Constants.OPTIONAL_SIGNAL.index(row['Optional Signal'])
            ch.dtmf_id_idx = int(row['DTMF ID'])
            ch.tone2_id_idx = int(row['2Tone ID'])
            ch.tone5_id_idx = int(row['5Tone ID'])
            ch.ptt_id = ['Off', 'Start', 'End', 'Start&End'].index(row['PTT ID'])
            ch.rx_color_code_idx = int(row['RX Color Code']) - 1
            ch.time_slot = int(row['Slot']) - 1
            ch.scan_list_name = row['Scan List']
            ch.receive_group_list_name = row['Receive Group List']
            ch.ptt_prohibit = row['PTT Prohibit'] == 'On'
            ch.reverse = row['Reverse'] == 'On'
            # TODO: = row['Simplex TDMA'] == 'On'
            ch.slot_suit = row['Slot Suit'] == 'On'
            # TODO:  = row['AES Digital Encryption'] == ''
            # TODO:  = row['Digital Encryption'] == ''
            ch.call_confirmation = row['Call Confirmation'] == 'On'
            ch.talkaround = row['Talk Around(Simplex)'] == 'On'
            ch.work_alone = row['Work Alone'] == 'On'
            # TODO:  = row['Custom CTCSS'] == ''
            ch.tone2_decode = row['2TONE Decode'] - 1
            ch.ranging = row['Ranging'] == 'On'
            # TODO:  = row['Through Mode'] == 'On'
            ch.aprs_rx = row['APRS RX'] == 'On'
            ch.analog_aprs_ptt_mode = Constants.ANALOG_APRS_PTT_MODE.index(row['Analog APRS PTT Mode'])
            ch.digital_aprs_ptt_mode = Constants.OFF_ON.index(row['Digital APRS PTT Mode'])
            ch.aprs_report_type = Constants.APRS_REPORT_TYPE.index(row['APRS Report Type'])
            ch.digital_aprs_report_channel = row['Digital APRS Report Channel']
            ch.sms_confirmation = row['SMS Confirmation'] == 'On'
            ch.exclude_channel_roaming = row['Exclude channel from roaming']
            ch.dmr_mode = row['DMR MODE']
            ch.data_ack_disable = row['DataACK Disable']
            ch.r5tone_bot = row['R5toneBot']
            ch.r5tone_eot = row['R5ToneEot']
            ch.auto_scan = row['Auto Scan']
            ch.analog_aprs_mute = row['Ana Aprs Mute']
            ch.send_talker_alias = row['Send Talker Alias']
            ch.analog_aprs_report_frequency_idx = row['AnaAprsTxPath']
            # TODO: ARC4
            # TODO: ex_emg_kind
            ch.tx_color_code_idx = int(row['TxCC']) - 1
    def importReceiveGroupCallListData(self, filepath):
        AnyToneMemory.initReceiveCallGroupLists()
        self.update2.emit(0, 1, "Importing Receive Group Call Lists")
        df = pd.read_csv(filepath)
        row_count = len(df)
        for index, row in df.iterrows():
            self.update2.emit(index, row_count, None)
            rgcl = ReceiveGroupCallList()
            rgcl.id = row['No.'] - 1
            rgcl.name = row['Group Name']
            rgcl.temp_tg_names = row['Contact'].split('|')
            rgcl.temp_tg_ids = row['Contact TG/DMR ID'].split('|')
            AnyToneMemory.receive_group_call_lists[rgcl.id] = rgcl
    def importZoneData(self, filepath):
        self.update2.emit(0, 1, "Importing Zones")
        df = pd.read_csv(filepath, keep_default_na=False, na_values=[])
        row_count = len(df)
        AnyToneMemory.initZones()
        for index, row in df.iterrows():
            self.update2.emit(index, row_count, None)
            zone = self.memory.zones[int(row['No.']) - 1]
            zone.name = row['Zone Name']
            zone_member_name_list = row['Zone Channel Member'].split('|')
            zone_member_rx_list = row['Zone Channel Member RX Frequency'].split('|')
            zone_member_tx_list = row['Zone Channel Member TX Frequency'].split('|')
            for i in range(len(zone_member_name_list)):
                zone_member_name = zone_member_name_list[i]
                zone_member_rx = int(Decimal(zone_member_rx_list[i]) * 100000)
                zone_member_tx = int(Decimal(zone_member_tx_list[i]) * 100000)
                ch: Channel = AnyToneMemory.findChannel(zone_member_name, zone_member_rx, zone_member_tx)
                if ch != None:
                    zone.temp_member_channels.append(ch.id)
            # A Channel
            zone_member_name = row['A Channel']
            zone_member_rx = int(Decimal(row['A Channel RX Frequency']) * 100000)
            zone_member_tx = int(Decimal(row['A Channel TX Frequency']) * 100000)
            ch: Channel = AnyToneMemory.findChannel(zone_member_name, zone_member_rx, zone_member_tx)
            try:
                zone.a_channel = zone.temp_member_channels.index(ch.id)
            except:
                pass
            # B Channel
            zone_member_name = row['B Channel']
            zone_member_rx = int(Decimal(row['B Channel RX Frequency']) * 100000)
            zone_member_tx = int(Decimal(row['B Channel TX Frequency']) * 100000)
            ch: Channel = AnyToneMemory.findChannel(zone_member_name, zone_member_rx, zone_member_tx)
            try:
                zone.b_channel = zone.temp_member_channels.index(ch.id)
            except:
                pass
            zone.hide = row['Zone Hide '] == '1'
    def importTalkGroupData(self, filepath):
        self.update2.emit(0, 1, "Importing TalkGroups")
        df = pd.read_csv(filepath, dtype=str, keep_default_na=False, na_values=[])
        row_count = len(df)
        AnyToneMemory.initTalkgroups()
        for index, row in df.iterrows():
            self.update2.emit(index, row_count, None)
            tg = self.memory.talkgroups[int(row['No.']) - 1]
            tg.tg_dmr_id = int(row['Radio ID'])
            tg.name = row['Name']
            tg.call_type = Constants.TG_CALL_TYPE.index(row['Call Type'])
            tg.call_alert = Constants.TG_CALL_ALERT.index(row['Call Alert'])
    def importScanListData(self, filepath):
        self.update2.emit(0, 1, "Importing Scan List")
        df = pd.read_csv(filepath, keep_default_na=False, na_values=[])
        row_count = len(df)
        AnyToneMemory.initScanLists()
        for index, row in df.iterrows():
            self.update2.emit(index, row_count, None)
            sl = self.memory.scanlist[int(row['No.']) - 1]
            sl.name = row['Scan List Name']
            ch_name_list = row['Scan Channel Member'].split('|')
            ch_rx_freq_list = row['Scan Channel Member RX Frequency'].split('|')
            ch_tx_freq_list = row['Scan Channel Member TX Frequency'].split('|')
            for i in range(len(ch_name_list)):
                member_name = ch_name_list[i]
                member_rx = int(Decimal(ch_rx_freq_list[i]) * 100000)
                member_tx = int(Decimal(ch_tx_freq_list[i]) * 100000)
                ch: Channel = AnyToneMemory.findChannel(member_name, member_rx, member_tx)
                if ch != None:
                    sl.temp_member_channels.append(ch.id)
            sl.scan_mode = Constants.SCAN_LIST_SCAN_MODE.index(row['Scan Mode'])
            sl.priority_channel_select = Constants.SCAN_LIST_PRIORITY_CHANNEL_SELECT.index(row['Priority Channel Select'])
            try:
                sl.priority_channel_1 = Constants.SCAN_LIST_PRIORITY_CHANNEL.index(row['Priority Channel 1'])
                if sl.priority_channel_1 == 0:
                    sl.priority_channel_1 = 0xffff
                else:
                    sl.priority_channel_1 = 0
            except:
                sl.priority_channel_1 = -1
                sl.temp_priority_1 = (row['Priority Channel 1'], int(Decimal(row['Priority Channel 1 RX Frequency']) * 100000), int(Decimal(row['Priority Channel 1 TX Frequency']) * 100000))
            try:
                sl.priority_channel_2 = Constants.SCAN_LIST_PRIORITY_CHANNEL.index(row['Priority Channel 2'])
                if sl.priority_channel_2 == 0:
                    sl.priority_channel_2 = 0xffff
                else:
                    sl.priority_channel_2 = 0
            except:
                sl.priority_channel_2 = -1
                sl.temp_priority_2 = (row['Priority Channel 2'], int(Decimal(row['Priority Channel 2 RX Frequency']) * 100000), int(Decimal(row['Priority Channel 2 TX Frequency']) * 100000))
            try:
                sl.revert_channel = Constants.SCAN_LIST_REVERT_CHANNEL.index(row['Revert Channel'])
            except:
                pass
            try:
                sl.look_back_time_a = Constants.SCAN_LIST_LOOK_BACK_TIME.index("{:.1f}".format(Decimal(row['Look Back Time A[s]'])))
            except:
                pass
            try:
                sl.look_back_time_b = Constants.SCAN_LIST_LOOK_BACK_TIME.index("{:.1f}".format(Decimal(row['Look Back Time B[s]'])))
            except:
                pass
            try:
                sl.dropout_delay_time = Constants.SCAN_LIST_DROPOUT_DELAY_DWELL_TIME.index("{:.1f}".format(Decimal(row['Dropout Delay Time[s]'])))
            except:
                pass
            try:
                sl.dwell_time = Constants.SCAN_LIST_DROPOUT_DELAY_DWELL_TIME.index("{:.1f}".format(Decimal(row['Dwell Time[s]'])))
            except:
                pass  
    def importDigitalContactData(self, filepath):
        self.update2.emit(0, 1, "Importing Digital Contacts")
        rows = 0
        AnyToneMemory.initDigitalContactList()
        chunksize = 10000
        df_idx = 0
        with pd.read_csv(filepath, dtype=str, keep_default_na=False, na_values=[], chunksize=chunksize) as reader:
            for df in reader:
                row_count = len(df)
                rows += row_count
        with pd.read_csv(filepath, dtype=str, keep_default_na=False, na_values=[], chunksize=chunksize) as reader:
            for df in reader:
                for index, row in df.iterrows():
                    self.update2.emit(index, rows, None)
                    dc = AnyToneMemory.digital_contact_list[int(row['No.']) - 1]
                    dc.radio_id = int(row['Radio ID'])
                    dc.callsign = row['Callsign']
                    dc.name = row['Name']
                    dc.city = row['City']
                    dc.state = row['State']
                    dc.country = row['Country']
                    dc.remarks = row['Remarks']
                    dc.call_type = Constants.TG_CALL_TYPE.index(row['Call Type'])
                    dc.call_alert = Constants.TG_CALL_ALERT.index(row['Call Alert'])
                df_idx += 1
    def importRoamingChannelData(self, filepath):
        self.update2.emit(0, 1, "Importing Roaming Channels")
        df = pd.read_csv(filepath, dtype=str)
        row_count = len(df)
        AnyToneMemory.initRoamingChannels()
        for index, row in df.iterrows():
            self.update2.emit(index, row_count, None)
            rc = self.memory.roaming_channels[int(row['No.']) - 1]
            rc.rx_frequency = int(Decimal(row['Receive Frequency']) * 100000)
            rc.tx_frequency = int(Decimal(row['Transmit Frequency']) * 100000)
            rc.color_code = Constants.ROAMING_CHANNEL_COLOR_CODE.index(row['Color Code'])
            rc.slot = Constants.ROAMING_CHANNEL_SLOT.index(row['Slot'])
            rc.name = row['Name']
    def importRoamingZoneData(self, filepath):
        self.update2.emit(0, 1, "Importing Roaming Zones")
        df = pd.read_csv(filepath, dtype=str)
        row_count = len(df)
        AnyToneMemory.initRoamingZones()
        for index, row in df.iterrows():
            self.update2.emit(index, row_count, None)
            rz = self.memory.roaming_zones[int(row['No.']) - 1]
            rz.name = row['Name']
            rz.temp_roaming_channels = row['Roaming Channel Member'].split('|')
    def importFMData(self, filepath):
        self.update2.emit(0, 1, "Importing FM Channels")
        df = pd.read_csv(filepath, dtype=str)
        row_count = len(df)
        AnyToneMemory.initFM()
        for index, row in df.iterrows():
            self.update2.emit(index, row_count, None)
            fm = self.memory.fm_channels[int(row['No.']) - 1]
            fm.frequency = int(Decimal(row['Frequency[MHz]']) * 10000)
            fm.scan_add = Constants.FM_SCAN.index(row['Scan'])
    def importPrefabricatedSMSData(self, filepath):
        self.update2.emit(0, 1, "Importing Prefabricated SMS")
        df = pd.read_csv(filepath, dtype=str, keep_default_na=False, na_values=[])
        row_count = len(df)
        AnyToneMemory.iniPrefabricatedSMS()
        for index, row in df.iterrows():
            self.update2.emit(index, row_count, None)
            sms = self.memory.prefabricated_sms_list[int(row['No.']) - 1]
            sms.text = row['Text']
    def importAutoRepeaterFrequencyData(self, filepath):
        self.update2.emit(0, 1, "Importing Auto Repeater Offset Frequencies")
        df = pd.read_csv(filepath, dtype=str, keep_default_na=False, na_values=[])
        row_count = len(df)
        AnyToneMemory.initAutoRepeaterOffsetFrequencies()
        for index, row in df.iterrows():
            self.update2.emit(index, row_count, None)
            arf = self.memory.auto_repeater_freq_list[int(row['No.']) - 1]
            arf.frequency = int(Decimal(row['Offset Frequency'].replace(' MHz', '')) * 100000)
class CSVImportWorker(QRunnable):
    signals = AnyToneMemorySignals()
    imports: list[(int, str)] = []
    import_index: int = 0
    def addImport(self, import_type: int, filepath: str):
        self.imports.append((import_type, filepath))
    def run(self):
        # print("Thread start")
        AnyToneMemory.signals = AnyToneMemorySignals()
        sf = CSVImport()
        sf.update1.connect(self.signals.update1)
        sf.update2.connect(self.signals.update2)
        AnyToneMemory.signals.update2.connect(self.signals.update2)
        self.imports.sort(key=lambda x: x[0])
        import_steps = len(self.imports) + 1
        step = 0
        for i, im in enumerate(self.imports):
            step += 1
            self.signals.update1.emit(i, import_steps, "Importing Data")
            if im[0] == MemoryController.RADIO_IDS:
                sf.importRadioIdData(im[1])
            elif im[0] == MemoryController.TALKGROUPS:
                sf.importTalkGroupData(im[1])
            elif im[0] == MemoryController.SCANLISTS:
                sf.importScanListData(im[1])
            elif im[0] == MemoryController.CHANNELS:
                sf.importChannelData(im[1])
            elif im[0] == MemoryController.ZONES:
                sf.importZoneData(im[1])
            elif im[0] == MemoryController.DIGITAL_CONTACT_LIST:
                sf.importDigitalContactData(im[1])
            elif im[0] == MemoryController.RECEIVE_GROUPCALL_LIST:
                sf.importReceiveGroupCallListData(im[1])
            elif im[0] == MemoryController.ROAMING_CHANNELS:
                sf.importRoamingChannelData(im[1])
            elif im[0] == MemoryController.ROAMING_ZONES:
                sf.importRoamingZoneData(im[1])
            elif im[0] == MemoryController.FM:
                sf.importFMData(im[1])
            elif im[0] == MemoryController.PREFAB_SMS:
                sf.importPrefabricatedSMSData(im[1])
            elif im[0] == MemoryController.AUTO_REPEATER_OFFSET_FREQ:
                sf.importAutoRepeaterFrequencyData(im[1])
        step += 1
        self.signals.update1.emit(step, import_steps, "Linking Data")
        AnyToneMemory.linkReferences()
        AnyToneMemory.signals = None
        self.signals.update1.emit(import_steps, import_steps, "Finished")
        # print("Thread complete")
        self.signals.finished.emit()

class SaveFile(MemoryController):
    def __init__(self):
        super().__init__()
        self.channel_count: int = 0
        self.channel_data: bytes = b''
        self.zone_count: int = 0
        self.zone_data: bytes = b''
        self.talkgroup_count: int = 0
        self.talkgroup_data: bytes = b''
        self.scanlist_count: int = 0
        self.scanlist_data: bytes = b''
        self.radioid_count: int = 0
        self.radioid_data: bytes = b''
    # Save Functions
    def createHeaders(self) -> bytes:
        data = b''
        data += struct.pack('10s5sB', Constants.RADIO_MODEL.encode('utf-8'), 
                               Constants.FW_CPS_VERSION.encode('utf-8'), AnyToneMemory.radio_mode)
        data += struct.pack('>2H3B', 
                                     self.channel_count,
                                     self.talkgroup_count,
                                     self.zone_count,
                                     self.scanlist_count,
                                     self.radioid_count
                                     )
        data += struct.pack('8x')
        return data
    def createChannelData(self):
        self.channel_data = b''
        self.channel_count = 0
        for i, ch in enumerate(AnyToneMemory.channels):
            if ch.rx_frequency != 0:
                self.channel_count += 1
                self.channel_data += ch.encodeStruct()
        return
    def createZoneData(self):
        self.zone_data = b''
        self.zone_count = 0
        for zone in AnyToneMemory.zones:
            if len(zone.channels) != 0:
                self.zone_count += 1
                self.zone_data += zone.encodeStruct()
        return
    def createScanListData(self):
        self.scanlist_data = b''
        self.scanlist_count = 0
        for scanlist in AnyToneMemory.scanlist:
            if len(scanlist.channels) != 0:
                self.scanlist_count += 1
                self.scanlist_data += scanlist.encodeStruct()
        return
    def createTalkGroupData(self):
        self.talkgroup_data = b''
        self.talkgroup_count = 0
        for talkgroup in AnyToneMemory.talkgroups:
            if talkgroup.tg_dmr_id != 0:
                self.talkgroup_count += 1
                self.talkgroup_data += talkgroup.encodeStruct()
        return
    def createRadioIdData(self):
        self.radioid_data = b''
        self.radioid_count = 0
        for radio_id in AnyToneMemory.radioid_list:
            if radio_id.dmr_id != 0:
                self.radioid_count += 1
                self.radioid_data += radio_id.encodeStruct()
        return
    def save(self, filepath):
        self.createChannelData()
        self.createZoneData()
        self.createScanListData()
        self.createTalkGroupData()
        self.createRadioIdData()
        with open(filepath, 'wb') as f:
            f.write(self.createHeaders())
            f.write(self.channel_data)
            f.write(self.zone_data)
            f.write(self.scanlist_data)
            f.write(self.talkgroup_data)
            f.write(self.radioid_data)
    # Open Functions
    def open(self, filepath):
        with open(filepath, 'rb') as f:
            # Read Headers
            self.readHeaders(f.read(0x17))
            f.read(0x8)
            # Channel Data
            channel_data_len = struct.calcsize(Channel.struct_format)
            for i in range(self.channel_count):
                ch = Channel()
                ch.decodeStruct(f.read(channel_data_len))
                AnyToneMemory.channels[ch.id] = ch
            # Zone Data
            zone_data_len = struct.calcsize(Zone.struct_format)
            for i in range(self.zone_count):
                z = Zone()
                z.decodeStruct(f.read(zone_data_len))
                for i in range(z.channel_count):
                    z.temp_member_channels.append(struct.unpack('<H', f.read(2))[0])
                AnyToneMemory.zones[z.id] = z
            # Scan List Data
            sl_data_len = struct.calcsize(ScanList.struct_format)
            for i in range(self.scanlist_count):
                sl = ScanList()
                sl.decodeStruct(f.read(sl_data_len))
                for i in range(sl.channel_count):
                    sl.temp_member_channels.append(struct.unpack('<H', f.read(2))[0])
                AnyToneMemory.scanlist[sl.id] = sl
            # TalkGroup Data
            tg_data_len = struct.calcsize(TalkGroup.struct_format)
            for i in range(self.talkgroup_count):
                tg = TalkGroup()
                tg.decodeStruct(f.read(tg_data_len))
                AnyToneMemory.talkgroups[tg.id] = tg
            # Radio ID Data
            rid_data_len = struct.calcsize(RadioID.struct_format)
            for i in range(self.radioid_count):
                rid = RadioID()
                rid.decodeStruct(f.read(rid_data_len))
                AnyToneMemory.radioid_list[rid.id] = rid
        AnyToneMemory.linkReferences()
    def readHeaders(self, data):
        radio_model, fw_version, radio_mode = struct.unpack('10s5sB', data[0x0:0x10])
        radio_model = radio_model.decode('utf-8').rstrip('\00')
        fw_version = fw_version.decode('utf-8').rstrip('\00')
        channel_count, talkgroup_count, zone_count, scanlist_count, radioid_count = struct.unpack('>2H3B', data[0x10:0x17])
        self.channel_count = channel_count
        self.talkgroup_count = talkgroup_count
        self.zone_count = zone_count
        self.scanlist_count = scanlist_count
        self.radioid_count = radioid_count
class SaveFileSignals(QObject):
    finished = Signal()
    update1 = Signal(int, int, str)
    update2 = Signal(int, int, str)
class SaveFileWorker(QRunnable):
    signals = SaveFileSignals()
    def run(self):
        sf = SaveFile()
        sf.update1.connect(self.signals.update1)
        sf.update2.connect(self.signals.update2)
        self.signals.finished.emit()

