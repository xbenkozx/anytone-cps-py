import struct, math
from decimal import Decimal
from pyaudio import PyAudio
from PySide6.QtCore import Qt, QObject, Signal
from CPS.Utils import Bit
# FW/CPS Version Data
class Constants:
    CPS_VERSION = "0.1"
    CPS_BUILD_NUMBER = "6"
    RADIO_MODEL = "D878UVII"
    FW_CPS_VERSION = "4.00"
    FW_CPS_VERSION_MODIFIER = 'Alpha'
    RADIO_VERSION = 'V101'
    HW_IDS = {'28e9:018a': 'D878UVII'}
    OFF_ON = ['Off', 'On']
    VF_MR = ['MEM', 'VFO']
    AT_OPTIONS = [
        'MODE 00000 Rx:400-480 136-174 Tx:400-480 136-174',
        'MODE 00001 Rx:400-480 136-174 Tx:400-480 136-174 (12.5KHz Only)',
        'MODE 00002 Rx:430-440 136-174 Tx:430-440 136-174',
        'MODE 00003 Rx:400-480 136-174 Tx:430-440 144-146',
        'MODE 00004 Rx:434-438 144-146 Tx:434-438 144-146',
        'MODE 00005 Rx:434-447 144-146 Tx:434-447 144-146',
        'MODE 00006 Rx:446-447 136-174 Tx:446-447 136-174',
        'MODE 00007 Rx:400-480 136-174 Tx:420-450 144-148',
        'MODE 00008 Rx:400-470 136-174 Tx:400-470 136-174',
        'MODE 00009 Rx:430-432 144-146 Tx:430-432 144-146',
        'MODE 00010 Rx:400-480 136-174 Tx:430-450 144-148',
        'MODE 00011 Rx:400-520 136-174 Tx:400-520 136-174',
        'MODE 00012 Rx:400-490 136-174 Tx:400-490 136-174',
        'MODE 00013 Rx:400-480 136-174 Tx:403-470 136-174',
        'MODE 00014 Rx:400-520 220-225 136-174 Tx:400-520 220-225 136-174',
        'MODE 00015 Rx:420-520 144-148 Tx:420-520 144-148',
        'MODE 00016 Rx:430-440 144-147 Tx:430-440 144-147',
        'MODE 00017 Rx:430-440 136-174 Tx:136-174',
        'MODE 00018 Rx:400-480 220-225 136-174 Tx:420-450 222-225 144-148'
    ]
    # Channel Options
    ChannelType = [
        'A-Analog',
        'D-Digital',
        'A+D TX A',
        'D+A TX D'
    ]
    TxPower = [
        'Low',
        'Mid',
        'High',
        'Turbo'
    ]
    BandWidth = [
        '12.5K',
        '25K'
    ]
    CTCSSCode = [ 
        '62.5', '67.0', '69.3', '71.9', '74.4', '77.0', '79.7', '82.5', 
        '85.4', '88.5', '91.5', '94.8', '97.4', '100.0', '103.5', '107.2', 
        '110.9', '114.8', '118.8', '123.0', '127.3', '131.8', '136.5', '141.3', 
        '146.2', '151.4', '156.7', '159.8', '162.2', '165.5', '167.9', '171.3', 
        '173.8', '177.3', '179.9', '183.5', '186.2', '189.9', '192.8', '196.6', 
        '199.5', '203.5', '206.5', '210.7', '218.1', '225.7', '229.1', '233.6', 
        '241.8', '250.3', '254.1', 'Custom CTCSS'
    ]
    DCSCode = [
        'D000N', 'D001N', 'D002N', 'D003N', 'D004N', 'D005N', 'D006N', 'D007N',
        'D010N', 'D011N', 'D012N', 'D013N', 'D014N', 'D015N', 'D016N', 'D017N',
        'D020N', 'D021N', 'D022N', 'D023N', 'D024N', 'D025N', 'D026N', 'D027N',
        'D030N', 'D031N', 'D032N', 'D033N', 'D034N', 'D035N', 'D036N', 'D037N',
        'D040N', 'D041N', 'D042N', 'D043N', 'D044N', 'D045N', 'D046N', 'D047N',
        'D050N', 'D051N', 'D052N', 'D053N', 'D054N', 'D055N', 'D056N', 'D057N',
        'D060N', 'D061N', 'D062N', 'D063N', 'D064N', 'D065N', 'D066N', 'D067N',
        'D070N', 'D071N', 'D072N', 'D073N', 'D074N', 'D075N', 'D076N', 'D077N',
        'D100N', 'D101N', 'D102N', 'D103N', 'D104N', 'D105N', 'D106N', 'D107N',
        'D110N', 'D111N', 'D112N', 'D113N', 'D114N', 'D115N', 'D116N', 'D117N',
        'D120N', 'D121N', 'D122N', 'D123N', 'D124N', 'D125N', 'D126N', 'D127N',
        'D130N', 'D131N', 'D132N', 'D133N', 'D134N', 'D135N', 'D136N', 'D137N',
        'D140N', 'D141N', 'D142N', 'D143N', 'D144N', 'D145N', 'D146N', 'D147N',
        'D150N', 'D151N', 'D152N', 'D153N', 'D154N', 'D155N', 'D156N', 'D157N',
        'D160N', 'D161N', 'D162N', 'D163N', 'D164N', 'D165N', 'D166N', 'D167N',
        'D170N', 'D171N', 'D172N', 'D173N', 'D174N', 'D175N', 'D176N', 'D177N',
        'D200N', 'D201N', 'D202N', 'D203N', 'D204N', 'D205N', 'D206N', 'D207N',
        'D210N', 'D211N', 'D212N', 'D213N', 'D214N', 'D215N', 'D216N', 'D217N',
        'D220N', 'D221N', 'D222N', 'D223N', 'D224N', 'D225N', 'D226N', 'D227N',
        'D230N', 'D231N', 'D232N', 'D233N', 'D234N', 'D235N', 'D236N', 'D237N',
        'D240N', 'D241N', 'D242N', 'D243N', 'D244N', 'D245N', 'D246N', 'D247N',
        'D250N', 'D251N', 'D252N', 'D253N', 'D254N', 'D255N', 'D256N', 'D257N',
        'D260N', 'D261N', 'D262N', 'D263N', 'D264N', 'D265N', 'D266N', 'D267N',
        'D270N', 'D271N', 'D272N', 'D273N', 'D274N', 'D275N', 'D276N', 'D277N',
        'D300N', 'D301N', 'D302N', 'D303N', 'D304N', 'D305N', 'D306N', 'D307N',
        'D310N', 'D311N', 'D312N', 'D313N', 'D314N', 'D315N', 'D316N', 'D317N',
        'D320N', 'D321N', 'D322N', 'D323N', 'D324N', 'D325N', 'D326N', 'D327N',
        'D330N', 'D331N', 'D332N', 'D333N', 'D334N', 'D335N', 'D336N', 'D337N',
        'D340N', 'D341N', 'D342N', 'D343N', 'D344N', 'D345N', 'D346N', 'D347N',
        'D350N', 'D351N', 'D352N', 'D353N', 'D354N', 'D355N', 'D356N', 'D357N',
        'D360N', 'D361N', 'D362N', 'D363N', 'D364N', 'D365N', 'D366N', 'D367N',
        'D370N', 'D371N', 'D372N', 'D373N', 'D374N', 'D375N', 'D376N', 'D377N',
        'D400N', 'D401N', 'D402N', 'D403N', 'D404N', 'D405N', 'D406N', 'D407N',
        'D410N', 'D411N', 'D412N', 'D413N', 'D414N', 'D415N', 'D416N', 'D417N',
        'D420N', 'D421N', 'D422N', 'D423N', 'D424N', 'D425N', 'D426N', 'D427N',
        'D430N', 'D431N', 'D432N', 'D433N', 'D434N', 'D435N', 'D436N', 'D437N',
        'D440N', 'D441N', 'D442N', 'D443N', 'D444N', 'D445N', 'D446N', 'D447N',
        'D450N', 'D451N', 'D452N', 'D453N', 'D454N', 'D455N', 'D456N', 'D457N',
        'D460N', 'D461N', 'D462N', 'D463N', 'D464N', 'D465N', 'D466N', 'D467N',
        'D470N', 'D471N', 'D472N', 'D473N', 'D474N', 'D475N', 'D476N', 'D477N',
        'D500N', 'D501N', 'D502N', 'D503N', 'D504N', 'D505N', 'D506N', 'D507N',
        'D510N', 'D511N', 'D512N', 'D513N', 'D514N', 'D515N', 'D516N', 'D517N',
        'D520N', 'D521N', 'D522N', 'D523N', 'D524N', 'D525N', 'D526N', 'D527N',
        'D530N', 'D531N', 'D532N', 'D533N', 'D534N', 'D535N', 'D536N', 'D537N',
        'D540N', 'D541N', 'D542N', 'D543N', 'D544N', 'D545N', 'D546N', 'D547N',
        'D550N', 'D551N', 'D552N', 'D553N', 'D554N', 'D555N', 'D556N', 'D557N',
        'D560N', 'D561N', 'D562N', 'D563N', 'D564N', 'D565N', 'D566N', 'D567N',
        'D570N', 'D571N', 'D572N', 'D573N', 'D574N', 'D575N', 'D576N', 'D577N',
        'D600N', 'D601N', 'D602N', 'D603N', 'D604N', 'D605N', 'D606N', 'D607N',
        'D610N', 'D611N', 'D612N', 'D613N', 'D614N', 'D615N', 'D616N', 'D617N',
        'D620N', 'D621N', 'D622N', 'D623N', 'D624N', 'D625N', 'D626N', 'D627N',
        'D630N', 'D631N', 'D632N', 'D633N', 'D634N', 'D635N', 'D636N', 'D637N',
        'D640N', 'D641N', 'D642N', 'D643N', 'D644N', 'D645N', 'D646N', 'D647N',
        'D650N', 'D651N', 'D652N', 'D653N', 'D654N', 'D655N', 'D656N', 'D657N',
        'D660N', 'D661N', 'D662N', 'D663N', 'D664N', 'D665N', 'D666N', 'D667N',
        'D670N', 'D671N', 'D672N', 'D673N', 'D674N', 'D675N', 'D676N', 'D677N',
        'D700N', 'D701N', 'D702N', 'D703N', 'D704N', 'D705N', 'D706N', 'D707N',
        'D710N', 'D711N', 'D712N', 'D713N', 'D714N', 'D715N', 'D716N', 'D717N',
        'D720N', 'D721N', 'D722N', 'D723N', 'D724N', 'D725N', 'D726N', 'D727N',
        'D730N', 'D731N', 'D732N', 'D733N', 'D734N', 'D735N', 'D736N', 'D737N',
        'D740N', 'D741N', 'D742N', 'D743N', 'D744N', 'D745N', 'D746N', 'D747N',
        'D750N', 'D751N', 'D752N', 'D753N', 'D754N', 'D755N', 'D756N', 'D757N',
        'D760N', 'D761N', 'D762N', 'D763N', 'D764N', 'D765N', 'D766N', 'D767N',
        'D770N', 'D771N', 'D772N', 'D773N', 'D774N', 'D775N', 'D776N', 'D777N',
        'D000I', 'D001I', 'D002I', 'D003I', 'D004I', 'D005I', 'D006I', 'D007I',
        'D010I', 'D011I', 'D012I', 'D013I', 'D014I', 'D015I', 'D016I', 'D017I',
        'D020I', 'D021I', 'D022I', 'D023I', 'D024I', 'D025I', 'D026I', 'D027I',
        'D030I', 'D031I', 'D032I', 'D033I', 'D034I', 'D035I', 'D036I', 'D037I',
        'D040I', 'D041I', 'D042I', 'D043I', 'D044I', 'D045I', 'D046I', 'D047I',
        'D050I', 'D051I', 'D052I', 'D053I', 'D054I', 'D055I', 'D056I', 'D057I',
        'D060I', 'D061I', 'D062I', 'D063I', 'D064I', 'D065I', 'D066I', 'D067I',
        'D070I', 'D071I', 'D072I', 'D073I', 'D074I', 'D075I', 'D076I', 'D077I',
        'D100I', 'D101I', 'D102I', 'D103I', 'D104I', 'D105I', 'D106I', 'D107I',
        'D110I', 'D111I', 'D112I', 'D113I', 'D114I', 'D115I', 'D116I', 'D117I',
        'D120I', 'D121I', 'D122I', 'D123I', 'D124I', 'D125I', 'D126I', 'D127I',
        'D130I', 'D131I', 'D132I', 'D133I', 'D134I', 'D135I', 'D136I', 'D137I',
        'D140I', 'D141I', 'D142I', 'D143I', 'D144I', 'D145I', 'D146I', 'D147I',
        'D150I', 'D151I', 'D152I', 'D153I', 'D154I', 'D155I', 'D156I', 'D157I',
        'D160I', 'D161I', 'D162I', 'D163I', 'D164I', 'D165I', 'D166I', 'D167I',
        'D170I', 'D171I', 'D172I', 'D173I', 'D174I', 'D175I', 'D176I', 'D177I',
        'D200I', 'D201I', 'D202I', 'D203I', 'D204I', 'D205I', 'D206I', 'D207I',
        'D210I', 'D211I', 'D212I', 'D213I', 'D214I', 'D215I', 'D216I', 'D217I',
        'D220I', 'D221I', 'D222I', 'D223I', 'D224I', 'D225I', 'D226I', 'D227I',
        'D230I', 'D231I', 'D232I', 'D233I', 'D234I', 'D235I', 'D236I', 'D237I',
        'D240I', 'D241I', 'D242I', 'D243I', 'D244I', 'D245I', 'D246I', 'D247I',
        'D250I', 'D251I', 'D252I', 'D253I', 'D254I', 'D255I', 'D256I', 'D257I',
        'D260I', 'D261I', 'D262I', 'D263I', 'D264I', 'D265I', 'D266I', 'D267I',
        'D270I', 'D271I', 'D272I', 'D273I', 'D274I', 'D275I', 'D276I', 'D277I',
        'D300I', 'D301I', 'D302I', 'D303I', 'D304I', 'D305I', 'D306I', 'D307I',
        'D310I', 'D311I', 'D312I', 'D313I', 'D314I', 'D315I', 'D316I', 'D317I',
        'D320I', 'D321I', 'D322I', 'D323I', 'D324I', 'D325I', 'D326I', 'D327I',
        'D330I', 'D331I', 'D332I', 'D333I', 'D334I', 'D335I', 'D336I', 'D337I',
        'D340I', 'D341I', 'D342I', 'D343I', 'D344I', 'D345I', 'D346I', 'D347I',
        'D350I', 'D351I', 'D352I', 'D353I', 'D354I', 'D355I', 'D356I', 'D357I',
        'D360I', 'D361I', 'D362I', 'D363I', 'D364I', 'D365I', 'D366I', 'D367I',
        'D370I', 'D371I', 'D372I', 'D373I', 'D374I', 'D375I', 'D376I', 'D377I',
        'D400I', 'D401I', 'D402I', 'D403I', 'D404I', 'D405I', 'D406I', 'D407I',
        'D410I', 'D411I', 'D412I', 'D413I', 'D414I', 'D415I', 'D416I', 'D417I',
        'D420I', 'D421I', 'D422I', 'D423I', 'D424I', 'D425I', 'D426I', 'D427I',
        'D430I', 'D431I', 'D432I', 'D433I', 'D434I', 'D435I', 'D436I', 'D437I',
        'D440I', 'D441I', 'D442I', 'D443I', 'D444I', 'D445I', 'D446I', 'D447I',
        'D450I', 'D451I', 'D452I', 'D453I', 'D454I', 'D455I', 'D456I', 'D457I',
        'D460I', 'D461I', 'D462I', 'D463I', 'D464I', 'D465I', 'D466I', 'D467I',
        'D470I', 'D471I', 'D472I', 'D473I', 'D474I', 'D475I', 'D476I', 'D477I',
        'D500I', 'D501I', 'D502I', 'D503I', 'D504I', 'D505I', 'D506I', 'D507I',
        'D510I', 'D511I', 'D512I', 'D513I', 'D514I', 'D515I', 'D516I', 'D517I',
        'D520I', 'D521I', 'D522I', 'D523I', 'D524I', 'D525I', 'D526I', 'D527I',
        'D530I', 'D531I', 'D532I', 'D533I', 'D534I', 'D535I', 'D536I', 'D537I',
        'D540I', 'D541I', 'D542I', 'D543I', 'D544I', 'D545I', 'D546I', 'D547I',
        'D550I', 'D551I', 'D552I', 'D553I', 'D554I', 'D555I', 'D556I', 'D557I',
        'D560I', 'D561I', 'D562I', 'D563I', 'D564I', 'D565I', 'D566I', 'D567I',
        'D570I', 'D571I', 'D572I', 'D573I', 'D574I', 'D575I', 'D576I', 'D577I',
        'D600I', 'D601I', 'D602I', 'D603I', 'D604I', 'D605I', 'D606I', 'D607I',
        'D610I', 'D611I', 'D612I', 'D613I', 'D614I', 'D615I', 'D616I', 'D617I',
        'D620I', 'D621I', 'D622I', 'D623I', 'D624I', 'D625I', 'D626I', 'D627I',
        'D630I', 'D631I', 'D632I', 'D633I', 'D634I', 'D635I', 'D636I', 'D637I',
        'D640I', 'D641I', 'D642I', 'D643I', 'D644I', 'D645I', 'D646I', 'D647I',
        'D650I', 'D651I', 'D652I', 'D653I', 'D654I', 'D655I', 'D656I', 'D657I',
        'D660I', 'D661I', 'D662I', 'D663I', 'D664I', 'D665I', 'D666I', 'D667I',
        'D670I', 'D671I', 'D672I', 'D673I', 'D674I', 'D675I', 'D676I', 'D677I',
        'D700I', 'D701I', 'D702I', 'D703I', 'D704I', 'D705I', 'D706I', 'D707I',
        'D710I', 'D711I', 'D712I', 'D713I', 'D714I', 'D715I', 'D716I', 'D717I',
        'D720I', 'D721I', 'D722I', 'D723I', 'D724I', 'D725I', 'D726I', 'D727I',
        'D730I', 'D731I', 'D732I', 'D733I', 'D734I', 'D735I', 'D736I', 'D737I',
        'D740I', 'D741I', 'D742I', 'D743I', 'D744I', 'D745I', 'D746I', 'D747I',
        'D750I', 'D751I', 'D752I', 'D753I', 'D754I', 'D755I', 'D756I', 'D757I',
        'D760I', 'D761I', 'D762I', 'D763I', 'D764I', 'D765I', 'D766I', 'D767I',
        'D770I', 'D771I', 'D772I', 'D773I', 'D774I', 'D775I', 'D776I', 'D777I'
    ]
    ANALOG_APRS_PTT_MODE = ['Off', 'Start of Transmission', 'End of Transmission']
    APRS_REPORT_TYPE = ['Off', 'Analog', 'Digital']
    OPTIONAL_SIGNAL = ['Off', 'DTMF', '2Tone', '5Tone']
    # TalkGroup Options
    TG_CALL_TYPE = [
        'Private Call',
        'Group Call',
        'All Call'
    ]
    TG_CALL_ALERT = [
        'None',
        'Online Alert'
    ]
    # Scan List Options
    SCAN_LIST_SCAN_MODE = [
        'Off'
    ]
    SCAN_LIST_PRIORITY_CHANNEL_SELECT = [
        'Off',
        'Priority Channel Select1',
        'Priority Channel Select2',
        'Priority Channel Select1 + Priority Channel Select2'
    ]
    SCAN_LIST_PRIORITY_CHANNEL = [
        'Off',
        'Current Channel'
        # This will extend with channel names in scan list
    ]
    SCAN_LIST_REVERT_CHANNEL = [
        'Selected',
        'Selected + TalkBack',
        'Last Called',
        'Last Used'
    ]
    SCAN_LIST_LOOK_BACK_TIME = []
    for i in range(5, 50):
        SCAN_LIST_LOOK_BACK_TIME.append(str(i/10))
    SCAN_LIST_DROPOUT_DELAY_DWELL_TIME = []
    for i in range(1, 50):
        SCAN_LIST_DROPOUT_DELAY_DWELL_TIME.append(str(i/10))
    # Optional Settings
    ## Power-On
    POWERON_INTERFACE = [
        'Default Interface',
        'Custom Char',
        'Custom Picture'
    ]
    AUTOSHUTDOWN = [
        'Off',
        '10m',
        '30m',
        '60m',
        '120m'
    ]
    ## Power Save
    POWER_SAVE = [
        'Off',
        '1:1',
        '2:1'
    ]
    AUTOSHUTDOWN_TYPE = [
        'is affected by call',
        'is not affected by call'
    ]
    ## Display
    BRIGHTNESS = ['1', '2', '3', '4', '5']
    AUTO_BACKLIGHT_DURATION = [
        'Always',
        '5s',
        '10s',
        '15s',
        '20s',
        '25s',
        '30s',
        '1m',
        '2m',
        '3m',
        '4m',
        '5m',
        '15m',
        '30m',
        '45m',
        '60m'
    ]
    BACKLIGHT_DELAY_TX = [
        'Off', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', 
        '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30'
    ]
    MENU_EXIT_TIME = ['5', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55', '60']
    LAST_CALLER = [
        'Off',
        'Display ID',
        'Display Callsign',
        'Show Both'
    ]
    CALL_DISPLAY_MODE = [
        'Turn off Talker Alias',
        'Call Sign Based',
        'Name Based'
    ]
    COLOR1 = [
        'Orange',
        'Red',
        'Yellow',
        'Green',
        'Turquiose',
        'Blue',
        'White'
    ]
    COLOR2 = [
        'White',
        'Black',
        'Orange',
        'Red',
        'Yellow',
        'Green',
        'Turquiose',
        'Blue'
    ]
    DISPLAY_CHANNEL_NUMBER = ['Actual Channel Number', 'Sequence Number In Zone']
    DISPLAY_STANDBY_PICTURE = [
        'Default',
        'Custom1',
        'Custom2'
    ]
    BACKLIGHT_DELAY_RX = [
        'Always', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', 
        '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30'
    ]
    DATE_DISPLAY_FORMAT = ['yyyy/m/d', 'd/m/yyyy']
    ## Work Mode
    DISPLAY_MODE = ['Channel', 'Frequency']
    MAIN_CHANNEL_SET = ['A', 'B']
    WORKING_MODE = ['Amateur', 'Professional']
    ## VOX/BT
    VOX_LEVEL = ['Off', '1', '2', '3']
    VOX_DELAY = [format(f'{Decimal(d)/10:.1f}s') for d in range(5, 30)]
    VOX_DETECTION = ['Built-in Microphone', 'External Microphone', 'Both']
    BT_GAIN = ['1', '2', '3', '4', '5']
    BT_HOLD_TIME = [
        'Off', '1s', '2s', '3s', '4s', '5s', '6s', '7s', '8s', '9s', '10s',
        '11s', '12s', '13s', '14s', '15s', '16s', '17s', '18s', '19s', '20s', 
        '21s', '22s', '23s', '24s', '25s', '26s', '27s', '28s', '29s', '30s', 
        '60s', '120s', 'Infinite'
        ]
    BT_RX_DELAY = ['30ms', '1.0s', '1.5s', '2.0s', '2.5s', '3.0s', '3.5s', '4.0s', '4.5s', '5.0s', '5.5s']
    BT_PTT_SLEEP = ['Infinity', '1min', '2min', '3min', '4min']
    ## STE
    STE_CTCSS_TYPE = ['Off', 'Silent', '120 Degree', '180 Degree', '240 Degree']
    STE_NO_SIGNAL = ['Off', '55.2Hz', '259.2Hz']
    STE_TIME = [str(i) + 'MS' for i in range(10, 1000, 10)]
    ## FM
    ## Key Function
    KEY_LOCK = ['Manual', 'Auto']
    KEY_FUNCTION = [
        'Off', 'Voltage', 'Power', 'Talk Around', 'Reverse', 'Digital Encryption', 'Call', 'VOX', 'V/M', 'Sub PTT', 'Scan', 'FM', 'Alarm', 'Record Switch', 'Record', 'SMS',
        'Dial', 'GPS Information', 'Monitor', 'Main Channel Switch', 'Hot Key 1', 'Hot Key 2', 'Hot Key 3', 'Hot Key 4', 'Hot Key 5', 'Hot Key 6', 'Work Alone', 'Nuisance Delete',
        'Digital Monitor', 'Sub CH Switch', 'Priority Zone', 'VFO Scan', 'Mic Sound Quality', 'Last Call Reply', 'Channel Type Switch', 'Ranging', 'Roaming', 'Channel Ranging',
        'Max Volume', 'Slot Switch', 'APRS Type Switch', 'Zone Select', 'Time Roaming Set', 'APRS Set', 'Mute Timing', 'CTC/DCS Set', 'TBST Send', 'BT Wireless', 'GPS', 'Ch. Name',
        'CDT Scan', 'APRS Send', 'Ana APRS Info', 'GPS Roaming', 'Dim Shut', 'Satellite Predicting', 'ANA SQL']
    LONG_KEY_TIME = ['1', '2', '3', '4', '5']
    # Other
    TOT = ['Off', '30s', '60s', '90s', '120s', '150s', '180s', '210s', '240s']
    LANGUAGE = ['English', 'German']
    FREQUENCY_STEP = ['2.5K', '5K', '6.25K', '8.33K', '10K', '12.5K', '20K', '25K', '30K', '50K']
    SQL_LEVEL = ['OFF', '1', '2', '3', '4', '5']
    TBST = ['1000Hz', '1450Hz', '1750Hz', '2100Hz']
    ANALOG_CALL_HOLD_TIME = [str(i) for i in range(30)]
    MUTE_TIMING = [str(i+1) + "minute" for i in range(255)]
    ENCRYPTION_TYPE = ['Common', 'Extended']
    # Digital Func
    TG_HOLD_TIME = [str(i+1) + 's' for i in range(0, 30)] + ['30min', 'Infinite']
    VOICE_HEADER_REPETITIONS = [str(i) for i in range(2, 8)]
    TX_PREAMBLE_DURATION = [str(i) + 'ms' for i in range(0, 2400, 60)]
    DIGITAL_MONITOR = ['Off', 'Single Slot', 'Double Slot']
    DIGITAL_MONITOR_CC = ['Any', 'Same']
    SMS_FORMAT = ['M-SMS', 'H-SMS', 'DMR Standard', 'Customer DMR']
    # Alert Tone
    ALERT = ['None', 'Ring']
    TALK_PERMIT = ['Off', 'Digital', 'Analog', 'Digital & Analog']
    DIGITAL_IDLE_TONE = ['Off', 'Type 1', 'Type 2', 'Type 3']
    KEY_TONE_SOUND_ADJUSTABLE = ['Adjustable'] + [str(i) for i in range(1, 15)]
    # GPS
    TIME_ZONE = [
        'GMT-12:00', 'GMT-11:30', 'GMT-11:00', 'GMT-10:30', 'GMT-10:00', 'GMT-09:30', 'GMT-09:00', 'GMT-08:30', 'GMT-08:00', 'GMT-07:30', 'GMT-07:00', 
        'GMT-06:30', 'GMT-06:00', 'GMT-05:30', 'GMT-05:00', 'GMT-04:30', 'GMT-04:00', 'GMT-03:30', 'GMT-03:00', 'GMT-02:30', 'GMT-02:00', 'GMT-01:30', 
        'GMT-01:00', 'GMT-00:30', 'GMT', 'GMT+00:30', 'GMT+01:00', 'GMT+01:30', 'GMT+02:00', 'GMT+02:30', 'GMT+03:00', 'GMT+03:30', 'GMT+04:00', 
        'GMT+04:30', 'GMT+05:00', 'GMT+05:30', 'GMT+06:00', 'GMT+06:30', 'GMT+07:00', 'GMT+07:30', 'GMT+08:00', 'GMT+08:30', 'GMT+09:00', 'GMT+09:30', 
        'GMT+10:00', 'GMT+10:30', 'GMT+11:00', 'GMT+11:30', 'GMT+12:00', 'GMT+12:30', 'GMT+13:00'
        ]
    RANGING_INTERVAL = [str(i+1) for i in range(4, 255)]
    DISTANCE_UNIT = ['Metric', 'Inch System']
    GPS_MODE = ['GPS', 'BDS', 'GPS+BDS', 'GLONASS', 'GPS+GLON', 'BDS+GLON', 'ALL']
    # Auto Repeater
    AUTO_REPEATER_ENABLED = ['Off', 'Positive', 'Negative']
    AUTO_REPEATER_INTERVALS = [str(i) for i in range(5, 51, 5)]
    REPEATER_OUT_OF_RANGE_NOTIFY = ['Off', 'Bell', 'Voice']
    AUTO_ROAMING_START_CONDITION = ['Fixed Time', 'Out Of Range']
    ROAMING_EFFECT_WAIT_TIME = ['None'] + [str(i) for i in range(1, 31)]
    # VFO Scan
    VFO_SCAN_TYPE = ['TO', 'CO', 'SE']
    # Volume/Audio
    MAX_VOLUME = ['Indoors'] + [str(i+1) for i in range(8)]
    MIC_GAIN = ['1', '2', '3', '4', '5']
    # Roaming Channel
    ROAMING_CHANNEL_COLOR_CODE = [str(i) for i in range(15)] + ['No Use']
    ROAMING_CHANNEL_SLOT = ['Slot1', 'Slot2', 'No Use']
    #FM
    FM_SCAN = ['Del', 'Add']
    #Alarm Settings
    ANALOG_EMERGENCY_ALARM = [
        'Alarm', 
        'Transpond+Background',
        'Transpond+Alarm',
        'Both'
    ]
    ANALOG_EMERGENCY_ENI_SELECT = [
        'None',
        'DTMF',
        '5Tone'
    ]
    ALARM_DURATION = [str(i+1) for i in range(254)]
    ENI_SEND_SELECT = ['Assigned Channel', 'Selected Channel']
    WORK_ALONE_VOICE_SWITCH = [str(i+1) + 'm' for i in range(255)]
    WORK_ALONE_AREA_SWITCH = [str(i+1) + 's' for i in range(255)]
    WORK_ALONE_MIC_SWITCH = ['Key', 'Voice Transmit']
    DIGITAL_EMERGENCY_ALARM = [
        'Alarm', 
        'Transpond+Background',
        'Transpond+NoLocalAlarm',
        'Transpond+LocalAlarm'
    ]
    MAN_DOWN_DELAY = [str(i) for i in range(255)]

class AesEncryptionCode:
    struct_format = ''
    def __init__(self):
        self.index: int = 0
        self.id: int = 0
        self.key: str = ''
        self.key_length: int = 0
    def encodeStruct(self) -> bytes:
        pass
    def decodeStruct(self, data:bytes):
        pass
    def encode(self) -> bytes:
        data = bytearray(0x30)
        data[0] = self.id
        data[0x1:0x21] = bytes.fromhex(self.key.rjust(0x40, '0'))
        data[0x22] = len(self.key)
        return data
    def decode(self, data:bytes):
        self.id = data[0]
        self.key_length = data[0x22]
        if self.key_length > 0:
            self.key = data[1:0x21].hex()[-self.key_length:].upper()
class AlarmSettings:
    def __init__(self):
        self.analog_emergency_alarm: int = 0
        self.analog_eni_type: int = 0
        self.analog_emergency_id: int = 0
        self.analog_alarm_time: int = 0
        self.analog_tx_duration: int = 0
        self.analog_rx_duration: int = 0
        self.analog_eni_send: int = 0
        self.analog_emergency_channel: int = 0
        self.analog_emergency_cycle: int = 0
        self.work_mode_voice_switch: int = 0
        self.work_mode_area_switch: int = 0
        self.work_mode_mic_switch: int = 0
        self.digital_emergency_alarm: int = 0
        self.digital_alarm_time: int = 0
        self.digital_tx_duration: int = 0
        self.digital_rx_duration: int = 0
        self.digital_eni_send: int = 0
        self.digital_emergency_channel: int = 0
        self.digital_emergency_cycle: int = 0
        self.digital_tg_dmr_id: int = 0
        self.digital_call_type: int = 0
        self.receive_alarm: bool = False
        self.man_down: bool = False
        self.man_down_delay: int = 0
    def encodeStruct(self) -> bytes: # TODO
        pass
    def decodeStruct(self, data: bytes): # TODO
        pass
    def decode(self, data_0000: bytes, data_1400: bytes, data_1440: bytes):
        self.analog_emergency_alarm = data_1400[0x0]
        self.analog_eni_type = data_1400[0x1]
        self.analog_emergency_id = data_1400[0x2]
        self.analog_alarm_time = data_1400[0x3]
        self.analog_tx_duration = data_1400[0x4]
        self.analog_rx_duration = data_1400[0x5]
        self.analog_eni_send = data_1400[0x8]
        self.analog_emergency_channel = data_1400[0x6]
        self.analog_emergency_cycle = data_1400[0x9]
        self.work_mode_voice_switch = data_1400[0x12]
        self.work_mode_area_switch = data_1400[0x13]
        self.work_mode_mic_switch = data_1400[0x14]
        self.digital_emergency_alarm = data_1400[0xa]
        self.digital_alarm_time = data_1400[0xb]
        self.digital_tx_duration = data_1400[0xc]
        self.digital_rx_duration = data_1400[0xd]
        self.digital_eni_send = data_1400[0x10]
        self.digital_emergency_channel = data_1400[0xe]
        self.digital_emergency_cycle = data_1400[0x11]
        self.digital_tg_dmr_id = int(data_1440[0x23:0x27].hex())
        self.digital_call_type = data_1440[0x0]
        self.receive_alarm = data_1400[0x15]
        self.man_down = data_0000[0x24]
        self.man_down_delay = data_0000[0x4f]
# TODO
class AnalogAddressBookItem:
    struct_format = ''
    def __init__(self):
        pass
    def encodeStruct(self) -> bytes:
        pass
    def decodeStruct(self, data:bytes):
        pass
    def encode(self) -> bytes:
        pass
    def decode(self, data:bytes):
        pass
 # TODO
class AprsSettings:
    struct_format = ''
    def __init__(self):
        pass
    def encodeStruct(self) -> bytes:
        pass
    def decodeStruct(self, data:bytes):
        pass
    def encode(self) -> bytes:
        pass
    def decode(self, data:bytes):
        pass
 # TODO
class Arc4EncryptionCode:
    struct_format = ''
    def __init__(self):
        pass
    def encodeStruct(self) -> bytes:
        pass
    def decodeStruct(self, data:bytes):
        pass
    def encode(self) -> bytes:
        pass
    def decode(self, data:bytes):
        pass
class AutoRepeaterOffsetFrequency:
    struct_format = '<'
    def __init__(self):
        self.id: int = 0
        self.frequency: int = 0
    def getFrequencyDecimal(self) -> Decimal:
        return Decimal(self.frequency) / 100000
    def getFrequencyStr(self):
        return format(f'{self.getFrequencyDecimal():.5f}')
    def encodeStruct(self):
        pass
    def decodeStruct(self, data: bytes):
        pass
    def encode(self):
        return self.frequency.to_bytes(4, 'little')
    def decode(self, data: bytes):
        self.frequency = int.from_bytes(data, 'little')
class Channel:
    struct_format = '>H16sIBI6B3?B?BBBB?2B5H6B?BBBBBH2B??B?B???B?B??BBBB'
    def __init__(self):
        self.id: int = -1
        self.name : str = ''
        self.rx_frequency : str = 0
        self.offset : str = 0
        self.offset_direction: int = 0
        self.correct_frequency: int = 0
        self.band_width : int = 0
        self.tx_power : int = 0
        self.channel_type : int = 0
        self.talkaround : bool = False
        self.call_confirmation : bool = False
        self.ptt_prohibit : bool = False
        self.ctcss_dcs_decode : int = 0
        self.ctcss_dcs_encode : int = 0
        self.ctcss_decode_tone : int = 0
        self.ctcss_encode_tone : int = 0
        self.dcs_decode_tone : int = 0
        self.dcs_encode_tone : int = 0
        self.contact : int = 0
        self.radio_id_idx : int = 0
        self.squelch_mode : int = 0
        self.ptt_id : int = 0
        self.optional_signal : int = 0
        self.busy_lock : int = 0
        self.scan_list_idx : int = 0
        self.tone2_id_idx : int = 0
        self.tone5_id_idx : int = 0
        self.dtmf_id_idx : int = 0
        self.rx_color_code_idx : int = 0
        self.tx_color_code_idx : int = 0
        self.work_alone : bool = False
        self.slot_suit : bool = False
        self.dmr_mode_dcdm : int = 0
        self.time_slot : int = 0
        self.receive_group_list: ReceiveGroupCallList = None
        self.sms_confirmation : bool = False
        self.aes_encryption_idx : int = 0
        self.auto_scan : bool = False
        self.data_ack_disable : bool = False
        self.exclude_channel_roaming : bool = False
        self.dmr_mode : int = 0
        self.ranging : bool = 0
        self.extend_encryption : int = 0
        self.send_talker_alias : bool = False
        self.sms_forbid : bool = False
        self.aes_random_key : bool = False
        self.aes_multiple_key : bool = False
        self.arc4_encryption_key_idx: int = 0
        self.analog_aprs_report_frequency_idx: int = 0
        self.reverse: int = 0
        self.aprs_rx: bool = False
        self.analog_aprs_ptt_mode: int = 0
        self.digital_aprs_ptt_mode: int = 0
        self.aprs_report_type: int = 0
        self.analog_aprs_mute: bool = False
        self.digital_aprs_report_channel: int = 0
        self.tone2_decode: int = 0
        self.r5tone_bot: int = 0
        self.r5tone_eot: int = 0
        # TODO: Implement
        self.digital_encryption: int = 0
        # CPS Data Object
        self.scan_list: ScanList = None
        self.talkgroup_obj: TalkGroup = TalkGroup()
        self.radioid_obj: RadioID = RadioID()
        self.scan_list_name = None
        self.receive_group_list_name = None
        self.receive_group_list_idx = 0xff
        self.temp_talkgroup = ('', -1)
        self.temp_radio_id = ''
    def clear(self):
        self.id: int = -1
        self.rx_frequency : int = 0
        self.offset : int = 0
        self.offset_direction: int = 0
        self.correct_frequency: int = 0
        self.band_width : int = 0
        self.tx_power : int = 0
        self.channel_type : int = 0
        self.talkaround : bool = False
        self.call_confirmation : bool = False
        self.ptt_prohibit : bool = False
        self.ctcss_dcs_decode : int = 0
        self.ctcss_dcs_encode : int = 0
        self.ctcss_decode_tone : int = 0
        self.ctcss_encode_tone : int = 0
        self.dcs_decode_tone : int = 0
        self.dcs_encode_tone : int = 0
        self.contact : int = 0
        self.radio_id_idx : int = 0
        self.squelch_mode : int = 0
        self.ptt_id : int = 0
        self.optional_signal : int = 0
        self.busy_lock : int = 0
        self.scan_list_idx : int = 0
        self.tone2_id_idx : int = 0
        self.tone5_id_idx : int = 0
        self.dtmf_id_idx : int = 0
        self.rx_color_code_idx : int = 0
        self.tx_color_code_idx : int = 0
        self.work_alone : bool = False
        self.slot_suit : bool = False
        self.dmr_mode_dcdm : int = 0
        self.time_slot : int = 0
        self.sms_confirmation : bool = False
        self.aes_encryption_idx : int = 0
        self.auto_scan : bool = False
        self.data_ack_disable : bool = False
        self.exclude_channel_roaming : bool = False
        self.dmr_mode : int = 0
        self.ranging : bool = 0
        self.extend_encryption : int = 0
        self.send_talker_alias : bool = False
        self.sms_forbid : bool = False
        self.aes_random_key : bool = False
        self.aes_multiple_key : bool = False
        self.arc4_encryption_key_idx: int = 0
        self.analog_aprs_report_frequency_idx: int = 0
        self.reverse: int = 0
        self.aprs_rx: bool = False
        self.analog_aprs_ptt_mode: int = 0
        self.digital_aprs_ptt_mode: int = 0
        self.aprs_report_type: int = 0
        self.analog_aprs_mute: bool = False
        self.digital_aprs_report_channel: int = 0
        self.tone2_decode: int = 0
        self.r5tone_bot: int = 0
        self.r5tone_eot: int = 0
        self.digital_encryption: int = 0
        self.name : str = ''
        self.talkgroup_obj: TalkGroup = TalkGroup()
        self.radioid_obj: RadioID = RadioID()
        self.temp_talkgroup = ('', -1)
        self.temp_radio_id = ''
    def copy(self, channel):
        self.rx_frequency = channel.rx_frequency
        self.offset = channel.offset
        self.offset_direction = channel.offset_direction
        self.correct_frequency = channel.correct_frequency
        self.band_width = channel.band_width
        self.tx_power = channel.tx_power
        self.channel_type = channel.channel_type
        self.talkaround = channel.talkaround
        self.call_confirmation = channel.call_confirmation
        self.ptt_prohibit = channel.ptt_prohibit
        self.ctcss_dcs_decode = channel.ctcss_dcs_decode
        self.ctcss_dcs_encode = channel.ctcss_dcs_encode
        self.ctcss_decode_tone = channel.ctcss_decode_tone
        self.ctcss_encode_tone = channel.ctcss_encode_tone
        self.dcs_decode_tone = channel.dcs_decode_tone
        self.dcs_encode_tone = channel.dcs_encode_tone
        self.contact = channel.contact
        self.radio_id_idx = channel.radio_id_idx
        self.squelch_mode = channel.squelch_mode
        self.ptt_id = channel.ptt_id
        self.optional_signal = channel.optional_signal
        self.busy_lock = channel.busy_lock
        self.scan_list_idx = channel.scan_list_idx
        self.tone2_id_idx = channel.tone2_id_idx
        self.tone5_id_idx = channel.tone5_id_idx
        self.dtmf_id_idx = channel.dtmf_id_idx
        self.rx_color_code_idx = channel.rx_color_code_idx
        self.tx_color_code_idx = channel.tx_color_code_idx
        self.work_alone = channel.work_alone
        self.slot_suit = channel.slot_suit
        self.dmr_mode_dcdm = channel.dmr_mode_dcdm
        self.time_slot = channel.time_slot
        self.sms_confirmation = channel.sms_confirmation
        self.aes_encryption_idx = channel.aes_encryption_idx
        self.auto_scan = channel.auto_scan
        self.data_ack_disable = channel.data_ack_disable
        self.exclude_channel_roaming = channel.exclude_channel_roaming
        self.dmr_mode = channel.dmr_mode
        self.ranging = channel.ranging
        self.extend_encryption = channel.extend_encryption
        self.send_talker_alias = channel.send_talker_alias
        self.sms_forbid = channel.sms_forbid
        self.aes_random_key = channel.aes_random_key
        self.aes_multiple_key = channel.aes_multiple_key
        self.arc4_encryption_key_idx = channel.arc4_encryption_key_idx
        self.analog_aprs_report_frequency_idx = channel.analog_aprs_report_frequency_idx
        self.reverse = channel.reverse
        self.aprs_rx = channel.aprs_rx
        self.analog_aprs_ptt_mode = channel.analog_aprs_ptt_mode
        self.digital_aprs_ptt_mode = channel.digital_aprs_ptt_mode
        self.aprs_report_type = channel.aprs_report_type
        self.analog_aprs_mute = channel.analog_aprs_mute
        self.digital_aprs_report_channel = channel.digital_aprs_report_channel
        self.tone2_decode = channel.tone2_decode
        self.r5tone_bot = channel.r5tone_bot
        self.r5tone_eot = channel.r5tone_eot
        self.digital_encryption = channel.digital_encryption
        self.name = channel.name
        self.talkgroup_obj = channel.talkgroup_obj
        self.radioid_obj = channel.radioid_obj
        self.temp_talkgroup = channel.temp_talkgroup
        self.temp_radio_id = channel.temp_radio_id
    def getTxFrequency(self) -> int:
        tx_freq: int = self.rx_frequency
        if self.offset_direction == 1:
            tx_freq = self.rx_frequency + self.offset
        elif self.offset_direction == 2:
            tx_freq = self.rx_frequency - self.offset
        return tx_freq
    def getTxFrequencyDecimal(self) -> Decimal:
        return Decimal(self.getTxFrequency()) / 100000
    def getRxFrequencyDecimal(self) -> Decimal:
        return Decimal(self.rx_frequency) / 100000
    def getTxFrequencyStr(self):
        return str(self.getTxFrequencyDecimal()).ljust(9,'0')
    def getRxFrequencyStr(self):
        return format(f'{self.getRxFrequencyDecimal():.5f}')
    def setFrequency(self, rx_frequency: int, tx_frequency: int):
        self.rx_frequency = rx_frequency
        offset = tx_frequency - self.rx_frequency
        if offset < 0:
                self.offset_direction = 2
                self.offset = offset * -1
        elif offset > 0:
            self.offset_direction = 1
            self.offset = offset
        else:
            self.offset_direction = 0
            self.offset = 0
    def setFrequencyStr(self, rx_frequency: str, tx_frequency: str):
        rx_freq = int(Decimal(rx_frequency) * 100000)
        tx_freq = int(Decimal(tx_frequency) * 100000)
        self.setFrequency(rx_freq, tx_freq)
    def encodeStruct(self):
        # TODO: Review
        if self.receive_group_list != None:
            self.receive_group_call_list_idx = self.receive_group_list.id
        else:
            self.receive_group_call_list_idx = 0xff
        data = struct.pack('>H16sIBI6B3?B?BBBB?',
            # Common H16sIBI6B3?B?BBBB?
            self.id,
            self.name.encode('utf-8'),
            self.rx_frequency,
            self.offset_direction,
            self.offset,
            self.correct_frequency,
            self.band_width,
            self.tx_power,
            self.busy_lock,
            self.scan_list_idx,
            self.channel_type,
            self.talkaround,
            self.call_confirmation,
            self.ptt_prohibit,
            self.dmr_mode_dcdm,
            self.aprs_rx,
            self.analog_aprs_ptt_mode,
            self.digital_aprs_ptt_mode,
            self.digital_aprs_report_channel, 
            self.aprs_report_type,
            self.analog_aprs_mute,
            # Analog 2B5H6B?BBBB
            self.ctcss_dcs_decode,
            self.ctcss_dcs_encode,
            self.ctcss_decode_tone,
            self.ctcss_encode_tone,
            self.dcs_decode_tone,
            self.dcs_encode_tone,
            self.receive_group_call_list_idx,
            self.squelch_mode,
            self.ptt_id,
            self.optional_signal,
            self.tone2_id_idx,
            self.tone5_id_idx,
            self.dtmf_id_idx,
            self.reverse,
            self.tone2_decode,
            self.r5tone_bot,
            self.r5tone_eot,
            self.digital_encryption,
            # Digital BH2B??B?B???B?B??BBBB
            self.radio_id_idx,
            self.contact,
            self.rx_color_code_idx,
            self.tx_color_code_idx,
            self.work_alone,
            self.slot_suit,
            self.time_slot,
            self.sms_confirmation,
            self.aes_encryption_idx,
            self.auto_scan,
            self.data_ack_disable,
            self.exclude_channel_roaming,
            self.dmr_mode,
            self.ranging,
            self.extend_encryption,
            self.send_talker_alias,
            self.sms_forbid,
            self.aes_random_key,
            self.aes_multiple_key,
            self.arc4_encryption_key_idx,
            self.analog_aprs_report_frequency_idx   
        )
        return data
    def decodeStruct(self, data):
        fdata = struct.unpack(self.struct_format, data)
        self.id = fdata[0]
        self.name = fdata[1].decode('utf-8').rstrip('\x00')
        self.rx_frequency = fdata[2]
        self.offset_direction = fdata[3]
        self.offset = fdata[4]
        self.correct_frequency = fdata[5]
        self.band_width = fdata[6]
        self.tx_power = fdata[7]
        self.busy_lock = fdata[8]
        self.scan_list = fdata[9]
        self.channel_type = fdata[10]
        self.talkaround = fdata[11]
        self.call_confirmation = fdata[12]
        self.ptt_prohibit = fdata[13]
        self.dmr_mode_dcdm = fdata[14]
        self.aprs_rx = fdata[15]
        self.analog_aprs_ptt_mode = fdata[16]
        self.digital_aprs_ptt_mode = fdata[17]
        self.digital_aprs_report_channel = fdata[18]
        self.aprs_report_type = fdata[19]
        self.analog_aprs_mute = fdata[20]
        # Analog 2B5H6B?BBBB
        self.ctcss_dcs_decode = fdata[21]
        self.ctcss_dcs_encode = fdata[22]
        self.ctcss_decode_tone = fdata[23]
        self.ctcss_encode_tone = fdata[24]
        self.dcs_decode_tone = fdata[25]
        self.dcs_encode_tone = fdata[26]
        self.receive_group_call_list_idx = fdata[27]
        self.squelch_mode = fdata[28]
        self.ptt_id = fdata[29]
        self.optional_signal = fdata[30]
        self.tone2_id_idx = fdata[31]
        self.tone5_id_idx = fdata[32]
        self.dtmf_id_idx = fdata[33]
        self.reverse = fdata[34]
        self.tone2_decode = fdata[35]
        self.r5tone_bot = fdata[36]
        self.r5tone_eot = fdata[37]
        self.digital_encryption = fdata[38]
        # Digital
        self.radio_id_idx = fdata[39]
        self.contact = fdata[40]
        self.rx_color_code_idx = fdata[41]
        self.tx_color_code_idx = fdata[42]
        self.work_alone = fdata[43]
        self.slot_suit = fdata[44]
        self.time_slot = fdata[45]
        self.sms_confirmation = fdata[46]
        self.aes_encryption_idx = fdata[47]
        self.auto_scan = fdata[48]
        self.data_ack_disable = fdata[49]
        self.exclude_channel_roaming = fdata[50]
        self.dmr_mode = fdata[51]
        self.ranging = fdata[52]
        self.extend_encryption = fdata[53]
        self.send_talker_alias = fdata[54]
        self.sms_forbid = fdata[55]
        self.aes_random_key = fdata[56]
        self.aes_multiple_key = fdata[57]
        self.arc4_encryption_key_idx = fdata[58]
        self.analog_aprs_report_frequency_idx = fdata[59]
    def decode(self, primary_data : bytes = None, secondary_data : bytes = None):
        if primary_data != None:
            self.rx_frequency = int(primary_data[:4].hex())
            self.offset = int(primary_data[4:8].hex())
            self.offset_direction = (primary_data[8] >> 6) & 0x3
            self.band_width = (primary_data[8] >> 4) & 0x3
            self.tx_power = (primary_data[8] >> 2) & 0x3
            self.channel_type = primary_data[8] & 0x3
            self.talkaround = Bit.getBit(primary_data[9], 7)
            self.call_confirmation = Bit.getBit(primary_data[9], 6)
            self.ptt_prohibit = Bit.getBit(primary_data[9], 5)
            self.reverse = Bit.getBit(primary_data[9], 4)
            self.ctcss_dcs_encode = (primary_data[9] >> 2) & 0x3
            self.ctcss_dcs_decode = primary_data[9] & 0x3
            self.ctcss_encode_tone = primary_data[10]
            self.ctcss_decode_tone = primary_data[11]
            self.dcs_encode_tone = int.from_bytes(primary_data[12:14], 'little')
            self.dcs_decode_tone = int.from_bytes(primary_data[14:16], 'little')
            self.tone2_decode = primary_data[18]
            self.contact = int.from_bytes(primary_data[19:21], 'big')
            self.radio_id_idx = primary_data[24]            
            self.squelch_mode = (primary_data[25] >> 4) & 0x3
            self.ptt_id = primary_data[25] & 0x3
            self.optional_signal = (primary_data[26] >> 4) & 0x3
            self.busy_lock = primary_data[26] & 0x3
            self.scan_list_idx = primary_data[27]
            self.receive_group_call_list_idx = primary_data[28]
            self.tone2_id_idx = primary_data[29]
            self.tone5_id_idx = primary_data[30]
            self.dtmf_id_idx = primary_data[31]
            self.rx_color_code_idx = primary_data[32]
            self.work_alone = Bit.getBit(primary_data[33], 7)
            self.aprs_rx = Bit.getBit(primary_data[33], 5)
            self.slot_suit = Bit.getBit(primary_data[33], 4)
            self.dmr_mode_dcdm = (primary_data[33] >> 2) & 0x3
            self.time_slot = Bit.getBit(primary_data[33], 1)
            self.sms_confirmation = Bit.getBit(primary_data[33], 0)
            self.aes_encryption_idx = primary_data[34]
            self.name = primary_data[35:51].decode('utf-8').rstrip('\x00')
            self.auto_scan = Bit.getBit(primary_data[52], 4)
            self.data_ack_disable = Bit.getBit(primary_data[52], 3)
            self.exclude_channel_roaming = Bit.getBit(primary_data[52], 2)
            self.dmr_mode = Bit.getBit(primary_data[52], 1)
            self.ranging = Bit.getBit(primary_data[52], 0)
            self.aprs_report_type = primary_data[53]
            self.analog_aprs_ptt_mode = primary_data[54]
            self.digital_aprs_ptt_mode = primary_data[55]
            self.digital_aprs_report_channel = primary_data[56]
            self.correct_frequency = primary_data[57]
            self.digital_encryption = primary_data[58]
            self.extend_encryption = Bit.getBit(primary_data[59], 5)
            self.send_talker_alias = Bit.getBit(primary_data[59], 4)
            self.analog_aprs_mute = Bit.getBit(primary_data[59], 3)
            self.sms_forbid = Bit.getBit(primary_data[59], 2)
            self.aes_random_key = Bit.getBit(primary_data[59], 1)
            self.aes_multiple_key = Bit.getBit(primary_data[59], 0)
            self.analog_aprs_report_frequency_idx = primary_data[60]
            self.arc4_encryption_key_idx = primary_data[61]
            # Secondary Data
            if secondary_data != None:
                self.r5tone_bot = secondary_data[0]
                self.r5tone_eot = secondary_data[1]
                self.tx_color_code_idx = secondary_data[3]
        # if self.id == 0:
        #     self.decodeStruct(self.encodeStruct())
    def encode(self):
        # Receive Group Call List
        if self.receive_group_list != None:
            self.receive_group_call_list_idx = self.receive_group_list.id
        else:
            self.receive_group_call_list_idx = 0xff
        # Scan List
        if self.scan_list != None:
            self.scan_list_idx = self.scan_list.id
        else:
            self.scan_list_idx = 0xff
        # Talkgroup
        self.contact = self.talkgroup_obj.id
        # Radio ID
        self.radio_id_idx = self.radioid_obj.id
        # Primary Channel Data
        primary_data = bytearray(64)
        primary_data[0:4] = bytearray(bytes.fromhex(str(self.rx_frequency).rjust(8,'0')))
        primary_data[4:8] = bytearray(bytes.fromhex(str(self.offset).rjust(8,'0')))
        primary_data[8] = (self.offset_direction << 6) + (self.band_width << 4) + (self.tx_power << 2) + self.channel_type
        primary_data[9] = Bit.setBit(primary_data[9], 7, self.talkaround)
        primary_data[9] = Bit.setBit(primary_data[9], 6, self.call_confirmation)
        primary_data[9] = Bit.setBit(primary_data[9], 5, self.ptt_prohibit)
        primary_data[9] = Bit.setBit(primary_data[9], 4, self.reverse)
        primary_data[9] += (self.ctcss_dcs_encode & 0x3) << 2
        primary_data[9] += self.ctcss_dcs_decode & 0x3
        primary_data[10] = self.ctcss_encode_tone
        primary_data[11] = self.ctcss_decode_tone
        primary_data[12:14] = self.dcs_encode_tone.to_bytes(2, 'little')
        primary_data[14:16] = self.dcs_decode_tone.to_bytes(2, 'little')
        primary_data[16] = 0xcf
        primary_data[17] = 0x09
        primary_data[18] = self.tone2_decode
        primary_data[19:21] = bytearray(self.contact.to_bytes(2, 'big'))
        primary_data[24] = self.radio_id_idx
        primary_data[25] = Bit.setBit(primary_data[25], 4, self.squelch_mode)
        primary_data[25] = Bit.setBit(primary_data[25], 0, self.ptt_id)
        primary_data[26] = Bit.setBit(primary_data[26], 4, self.optional_signal)
        primary_data[26] = Bit.setBit(primary_data[26], 0, self.busy_lock)
        primary_data[27] = self.scan_list_idx
        primary_data[28] = self.receive_group_list_idx
        primary_data[29] = self.tone2_id_idx
        primary_data[30] = self.tone5_id_idx
        primary_data[31] = self.dtmf_id_idx
        primary_data[32] = self.rx_color_code_idx
        primary_data[33] = Bit.setBit(primary_data[33], 7, self.work_alone)
        primary_data[33] = Bit.setBit(primary_data[33], 5, self.aprs_rx)
        primary_data[33] = Bit.setBit(primary_data[33], 4, self.slot_suit)
        primary_data[33] += self.dmr_mode_dcdm << 2
        primary_data[33] = Bit.setBit(primary_data[33], 1, self.time_slot)
        primary_data[33] = Bit.setBit(primary_data[33], 0, self.sms_confirmation)
        primary_data[34] = self.aes_encryption_idx
        primary_data[35:51] = bytearray(self.name.encode('utf-8').ljust(16, b'\x00'))
        primary_data[52] = Bit.setBit(primary_data[52], 4, self.auto_scan)
        primary_data[52] = Bit.setBit(primary_data[52], 3, self.data_ack_disable)
        primary_data[52] = Bit.setBit(primary_data[52], 2, self.exclude_channel_roaming)
        primary_data[52] = Bit.setBit(primary_data[52], 1, self.dmr_mode)
        primary_data[52] = Bit.setBit(primary_data[52], 0, self.ranging)
        primary_data[53] = self.aprs_report_type
        primary_data[54] = self.analog_aprs_ptt_mode
        primary_data[55] = self.digital_aprs_ptt_mode
        primary_data[56] = self.digital_aprs_report_channel
        primary_data[57] = self.correct_frequency
        primary_data[58] = self.digital_encryption
        primary_data[59] = Bit.setBit(primary_data[59], 5, self.extend_encryption)
        primary_data[59] = Bit.setBit(primary_data[59], 4, self.send_talker_alias)
        primary_data[59] = Bit.setBit(primary_data[59], 3, self.analog_aprs_mute)
        primary_data[59] = Bit.setBit(primary_data[59], 2, self.sms_forbid)
        primary_data[59] = Bit.setBit(primary_data[59], 1, self.aes_random_key)
        primary_data[59] = Bit.setBit(primary_data[59], 0, self.aes_multiple_key)
        primary_data[60] = self.analog_aprs_report_frequency_idx
        primary_data[61] = self.arc4_encryption_key_idx
        # Secondary Channel Data
        secondary_data = bytearray(64)
        secondary_data[0] = self.r5tone_bot
        secondary_data[1] = self.r5tone_eot
        secondary_data[3] = self.tx_color_code_idx
        return bytes(primary_data), bytes(secondary_data)
class DTMFSettings:
    struct_format = ''
    def __init__(self):
        pass
    def encodeStruct(self) -> bytes:
        pass
    def decodeStruct(self, data:bytes):
        pass
    def encode(self) -> bytes:
        pass
    def decode(self, data:bytes):
        pass
class DigitalContact:
    struct_format = '<'
    def __init__(self):
        self.id: int = 0
        self.radio_id: int = 0
        self.callsign: str = ''
        self.name: str = ''
        self.city: str = ''
        self.state: str = ''
        self.country: str = ''
        self.remarks: str = ''
        self.call_type: int = -1
        self.call_alert: int = 0
    def encodeStruct(self):
        pass
    def decodeStruct(self, data: bytes):
        pass
    def encode(self):
        pass
    def decode(self, data: bytes):
        self.call_type = data[0]
        self.dmr_id = int(data[1:4].hex())
        self.call_alert = data[5]
        # print(strings) 
class ExpertOptions:
    def __init__(self):
        self.data: str = ''
        self.band_select: bool = False
        self.full_test_mode: bool = False
        self.chinese: bool = False
        self.area_code: str = ''
        self.manufacture_code: str = ''
        self.radio_type: str = ''
        self.band_settings_password: str = ''
        self.frequency_mode: int = 0
        self.program_password: str = ''
        self.serial_number: str = ''
        self.production_date: str = ''
        self.maintenance_date: str = ''
        self.maintenance_description: str = ''
        self.dealer_code: str = ''
        self.stock_date: str = ''
        self.sell_date: str = ''
        self.seller: str = ''
    def encode(self) -> bytes:
        data = bytearray(self.data)
        data[0x2] = Bit.setBit(data[0x2], 0, self.full_test_mode)
        data[0x3] = self.frequency_mode
        data[0x4] = Bit.setBit(data[0x4], 0, not self.chinese)
        data[0x5] = Bit.setBit(data[0x5], 0, not self.chinese)
        data[0x6] = Bit.setBit(data[0x6], 0, self.band_select)
        # data[0xb:0xf] = bytearray(self.band_settings_password.encode('utf-8').ljust(4, b'\x00'))
        # data[0x10:0x17] = bytearray(self.radio_type.encode('utf-8').ljust(7, b'\x00'))
        data[0x28:0x2c] = bytearray(self.program_password.encode('utf-8').ljust(4, b'\x00'))
        data[0x2c:0x30] = bytearray(self.area_code.encode('utf-8').ljust(4, b'\x00'))
        # self.data[0x30:0x40] = bytearray(self.serial_number.encode('utf-8').ljust(16, b'\x00'))
        # self.data[0x40:0x50] = bytearray(self.production_date.encode('utf-8').ljust(16, b'\x00'))
        data[0x50:0x58] = bytearray(self.manufacture_code.encode('utf-8').ljust(8, b'\x00'))
        data[0x60:0x70] = bytearray(self.maintenance_date.encode('utf-8').ljust(16, b'\x00'))
        data[0x70:0x80] = bytearray(self.dealer_code.encode('utf-8').ljust(16, b'\x00'))
        data[0x80:0x90] = bytearray(self.stock_date.encode('utf-8').ljust(16, b'\x00'))
        data[0x90:0xa0] = bytearray(self.sell_date.encode('utf-8').ljust(16, b'\x00'))
        data[0xa0:0xb0] = bytearray(self.seller.encode('utf-8').ljust(16, b'\x00'))
        data[0xb0:0x100] = bytearray(self.maintenance_description.encode('utf-8').ljust(0x50, b'\x00'))
        return bytes(data)
    def decode(self, data: bytes):
        self.full_test_mode = Bit.getBit(data[0x2], 0)
        self.frequency_mode = data[0x3]
        self.chinese = data[0x4] == 0 and data[0x5] == 0
        self.band_select = Bit.getBit(data[0x6], 0)
        self.band_settings_password = data[0xb: 0xf].decode('utf-8').rstrip('\x00')
        self.radio_type = data[0x10: 0x17].decode('utf-8').rstrip('\x00')
        self.program_password = data[0x28:0x2c].decode('utf-8').rstrip('\x00')
        self.area_code = data[0x2c:0x30].decode('utf-8').rstrip('\x00')
        self.serial_number = data[0x30:0x40].decode('utf-8').rstrip('\x00')
        self.production_date = data[0x40:0x50].decode('utf-8').rstrip('\x00')
        self.manufacture_code = data[0x50:0x58].decode('utf-8').rstrip('\x00')
        self.maintenance_date = data[0x60:0x70].decode('utf-8').rstrip('\x00')
        self.dealer_code = data[0x70:0x80].decode('utf-8').rstrip('\x00')
        self.stock_date = data[0x80:0x90].decode('utf-8').rstrip('\x00')
        self.sell_date = data[0x90:0xa0].decode('utf-8').rstrip('\x00')
        self.seller = data[0xa0:0xb0].decode('utf-8').rstrip('\x00')
        self.maintenance_description = data[0xb0:0x100].decode('utf-8').rstrip('\x00')
        self.data = data
class FM:
    struct_format = '<BI?'
    def __init__(self):
        self.id: int = 0
        self.frequency: int = 0
        self.scan_add: bool = True
    def getFrequencyDecimal(self) -> Decimal:
        return Decimal(self.frequency) / 10000
    def getFrequencyStr(self):
        return format(f'{self.getFrequencyDecimal():.2f}')
    def setFrequencyStr(self, freq_str: str):
        self.frequency = int(Decimal(freq_str) * 10000)
    def encodeStruct(self):
        return struct.pack(self.struct_format, 
                           self.id,
                           self.frequency,
                           self.scan_add)
    def decodeStruct(self, data: bytes):
        fdata = struct.unpack(self.struct_format, data)
        self.id = fdata[0]
        self.frequency = fdata[1]
        self.scan_add = fdata[2]
    def encode(self):
        pass
    def decode(self, data: bytes):
        pass
class GpsRoaming:
    def __init__(self):
        self.clear()
    def clear(self):
        self.id: int = 0
        self.enabled: int = 0
        self.zone_idx: int = 0xff
        self.lat_degree: int = 0
        self.lat_minute: int = 0
        self.lat_minute_decimal: int = 0
        self.north_south: int = 0
        self.long_degree: int = 0
        self.long_minute: int = 0
        self.long_minute_decimal: int = 0
        self.east_west: int = 0
        self.radius: int = 0
        self.zone: Zone = None
    def decode(self, data: bytes):
        self.enabled = data[0]
        self.zone_idx = data[1]
        self.lat_degree = data[2]
        self.lat_minute = data[3]
        self.lat_minute_decimal = data[4]
        self.north_south = data[5]
        self.long_degree = data[6]
        self.long_minute = data[7]
        self.long_minute_decimal = data[8]
        self.east_west = data[9]
        self.radius = int.from_bytes(data[12:16], 'little')
    def encode(self) -> bytes:
        data = bytearray(0x10)
        data[0] = self.enabled
        data[1] = self.zone_idx
        data[2] = self.lat_degree
        data[3] = self.lat_minute
        data[4] = self.lat_minute_decimal
        data[5] = self.north_south
        data[6] = self.long_degree
        data[7] = self.long_minute
        data[8] = self.long_minute_decimal
        data[9] = self.east_west
        data[12:16] = self.radius.to_bytes(4, 'little')
        return data
class MasterRadioId:
    def __init__(self):
        self.dmr_id: int = 0
        self.used: bool = False
        self.name: str = ''
    def encode(self) -> bytes:
        data = bytearray(0x20)
        data[0:4] = bytearray(bytes.fromhex(str(self.dmr_id).rjust(8,'0')))
        data[4] = self.used
        data[5:0x20] = self.name.encode('utf-8').ljust(27, b'\x00')
        return bytes(data)
    def decode(self, data: bytes):
        self.dmr_id = int(data[0:4].hex())
        self.used = int(data[4])
        self.name = data[5:0x20].decode('utf-8').rstrip('\x00')
class OptionalSettings():
    struct_format = '>'
    def __init__(self):
        # Power-on
        self.poweron_interface: int = 0
        self.poweron_display_1: bytearray = bytearray(14)
        self.poweron_display_2: bytearray = bytearray(14)
        self.poweron_password: int = 0
        self.poweron_password_char: str = ''
        self.default_startup_channel: int = 0
        self.startup_zone_a: int = 0
        self.startup_channel_a: int = 0
        self.startup_zone_b: int = 0
        self.startup_channel_b: int = 0
        self.startup_gps_test: int = 0
        self.startup_reset: int = 0
        # Power Save
        self.auto_shutdown: int = 0
        self.power_save: int = 0
        self.auto_shutdown_type: int = 0
        # Display
        self.brightness: int = 0
        self.auto_backlight_duration: int = 0
        self.backlight_tx_delay: int = 0
        self.menu_exit_time: int = 0
        self.time_display: int = 0
        self.last_caller: int = 0
        self.call_display_mode: int = 0
        self.callsign_display_color: int = 0
        self.call_end_prompt_box: int = 0
        self.display_channel_number: int = 0
        self.display_current_contact: int = 0
        self.standby_char_color: int = 0
        self.standby_bk_picture: int = 0
        self.show_last_call_on_launch: int = 0
        self.separate_display: int = 0
        self.ch_switching_keeps_caller: int = 0
        self.backlight_rx_delay: int = 0
        self.channel_name_color_a: int = 0
        self.channel_name_color_b: int = 0
        self.zone_name_color_a: int = 0
        self.zone_name_color_b: int = 0
        self.display_channel_type: int = 0
        self.display_time_slot: int = 0
        self.display_color_code: int = 0
        self.date_display_format: int = 0
        self.volume_bar: int = 0
        # Work Mode
        self.display_mode: int = 0
        self.vf_mr_a: int = 0
        self.vf_mr_b: int = 0
        self.mem_zone_a: int = 0
        self.mem_zone_b: int = 0
        self.main_channel_set: int = 0
        self.sub_channel_mode: int = 0
        self.working_mode: int = 0
        # Vox/BT
        self.vox_level: int = 0
        self.vox_delay: int = 0
        self.vox_detection: int = 0
        self.bt_on_off: int = 0
        self.bt_int_mic: int = 0
        self.bt_int_spk: int = 0
        self.bt_mic_gain: int = 0
        self.bt_spk_gain: int = 0
        self.bt_hold_time: int = 0
        self.bt_rx_delay: int = 0
        self.bt_ptt_hold: int = 0
        self.bt_ptt_sleep_time: int = 0
        # STE
        self.ste_type_of_ctcss: int = 0
        self.ste_when_no_signal: int = 0
        self.ste_time: int = 0
        # FM
        self.fm_vfo_mem: int = 0
        self.fm_work_channel: int = 0
        self.fm_monitor: int = 0
        # Key Function
        self.key_lock: int = 0
        self.pf1_short_key: int = 0
        self.pf2_short_key: int = 0
        self.pf3_short_key: int = 0
        self.p1_short_key: int = 0
        self.p2_short_key: int = 0
        self.pf1_long_key: int = 0
        self.pf2_long_key: int = 0
        self.pf3_long_key: int = 0
        self.p1_long_key: int = 0
        self.p2_long_key: int = 0
        self.long_key_time: int = 0
        self.knob_lock: int = 0
        self.keyboard_lock: int = 0
        self.side_key_lock: int = 0
        self.forced_key_lock: int = 0
        # Other
        self.address_book_sent_with_code: int = 0
        self.tot: int = 0
        self.language: int = 0
        self.frequency_step: int = 0
        self.sql_level_a: int = 0
        self.sql_level_b: int = 0
        self.tbst: int = 0
        self.analog_call_hold_time: int = 0
        self.call_channel_maintained: int = 0
        self.priority_zone_a: int = 0
        self.priority_zone_b: int = 0
        self.mute_timing: int = 0
        self.encryption_type: int = 0
        self.tot_predict: int = 0
        self.tx_power_agc: int = 0
        # Digital Func
        self.group_call_hold_time: int = 0
        self.private_call_hold_time: int = 0
        self.manual_dial_group_call_hold_time: int = 0
        self.manual_dial_private_call_hold_time: int = 0
        self.voice_header_repetitions: int = 0
        self.tx_preamble_duration: int = 0
        self.filter_own_id: int = 0
        self.digital_remote_kill: int = 0
        self.digital_monitor: int  = 0
        self.digital_monitor_cc: int = 0
        self.digital_monitor_id: int = 0
        self.monitor_slot_hold: int = 0
        self.remote_monitor: int = 0
        self.sms_format: int = 0
        # Alert Tone
        self.sms_alert: int = 0
        self.call_alert: int = 0
        self.digi_call_reset_tone: int = 0
        self.talk_permit: int = 0
        self.key_tone: int = 0
        self.digi_idle_channel_tone: int = 0
        self.startup_sound: int = 0
        self.tone_key_sound_adjustable: int = 0
        self.analog_idle_channel_tone: int = 0
        self.plugin_recording_tone: int = 0
        self.call_permit_first_tone_freq: int = 0
        self.call_permit_first_tone_period: int = 0
        self.call_permit_second_tone_freq: int = 0
        self.call_permit_second_tone_period: int = 0
        self.call_permit_third_tone_freq: int = 0
        self.call_permit_third_tone_period: int = 0
        self.call_permit_fourth_tone_freq: int = 0
        self.call_permit_fourth_tone_period: int = 0
        self.call_permit_fifth_tone_freq: int = 0
        self.call_permit_fifth_tone_period: int = 0
        self.idle_channel_first_tone_freq: int = 0
        self.idle_channel_first_tone_period: int = 0
        self.idle_channel_second_tone_freq: int = 0
        self.idle_channel_second_tone_period: int = 0
        self.idle_channel_third_tone_freq: int = 0
        self.idle_channel_third_tone_period: int = 0
        self.idle_channel_fourth_tone_freq: int = 0
        self.idle_channel_fourth_tone_period: int = 0
        self.idle_channel_fifth_tone_freq: int = 0
        self.idle_channel_fifth_tone_period: int = 0
        self.call_reset_first_tone_freq: int = 0
        self.call_reset_first_tone_period: int = 0
        self.call_reset_second_tone_freq: int = 0
        self.call_reset_second_tone_period: int = 0
        self.call_reset_third_tone_freq: int = 0
        self.call_reset_third_tone_period: int = 0
        self.call_reset_fourth_tone_freq: int = 0
        self.call_reset_fourth_tone_period: int = 0
        self.call_reset_fifth_tone_freq: int = 0
        self.call_reset_fifth_tone_period: int = 0
        # Alert Tone 1
        self.call_end_first_tone_freq: int = 0
        self.call_end_first_tone_period: int = 0
        self.call_end_second_tone_freq: int = 0
        self.call_end_second_tone_period: int = 0
        self.call_end_third_tone_freq: int = 0
        self.call_end_third_tone_period: int = 0
        self.call_end_fourth_tone_freq: int = 0
        self.call_end_fourth_tone_period: int = 0
        self.call_end_fifth_tone_freq: int = 0
        self.call_end_fifth_tone_period: int = 0
        self.call_all_first_tone_freq: int = 0
        self.call_all_first_tone_period: int = 0
        self.call_all_second_tone_freq: int = 0
        self.call_all_second_tone_period: int = 0
        self.call_all_third_tone_freq: int = 0
        self.call_all_third_tone_period: int = 0
        self.call_all_fourth_tone_freq: int = 0
        self.call_all_fourth_tone_period: int = 0
        self.call_all_fifth_tone_freq: int = 0
        self.call_all_fifth_tone_period: int = 0
        # GPS/Ranging
        self.gps_power: int = 0
        self.gps_positioning: int = 0
        self.time_zone: int = 0
        self.ranging_interval: int = 0
        self.distance_unit: int = 0
        self.gps_template_information: int = 0
        self.gps_information_char: str = ''
        self.gps_mode: int = 0
        self.gps_roaming: int = 0
        # VFO Scan
        self.vfo_scan_type: int = 0
        self.vfo_scan_start_freq_uhf: int = 0
        self.vfo_scan_end_freq_uhf: int = 0
        self.vfo_scan_start_freq_vhf: int = 0
        self.vfo_scan_end_freq_vhf: int = 0
        # Auto Repeater
        self.auto_repeater_a: int = 0
        self.auto_repeater_b: int = 0
        self.auto_repeater_1_uhf: int = 0xff
        self.auto_repeater_1_vhf: int = 0xff
        self.auto_repeater_2_uhf: int = 0xff
        self.auto_repeater_2_vhf: int = 0xff
        self.repeater_check: int = 0
        self.repeater_check_interval: int = 0
        self.repeater_check_reconnections: int = 0
        self.repeater_out_of_range_notify: int = 0
        self.out_of_range_notify: int = 0
        self.auto_roaming: int = 0
        self.auto_roaming_start_condition: int = 0
        self.auto_roaming_fixed_time: int = 0
        self.roaming_effect_wait_time: int = 0
        self.roaming_zone: int = 0
        self.auto_repeater_1_min_freq_vhf: int = 0
        self.auto_repeater_1_max_freq_vhf: int = 0
        self.auto_repeater_1_min_freq_uhf: int = 0
        self.auto_repeater_1_max_freq_uhf: int = 0
        self.auto_repeater_2_min_freq_vhf: int = 0
        self.auto_repeater_2_max_freq_vhf: int = 0
        self.auto_repeater_2_min_freq_uhf: int = 0
        self.auto_repeater_2_max_freq_uhf: int = 0
        # Record
        self.record_function: int = 0
        # Volume/Audio
        self.max_volume: int = 0
        self.max_headphone_volume: int = 0
        self.digi_mic_gain: int = 0
        self.enhanced_sound_quality: int = 0
        self.analog_mic_gain: int = 0
        # Unknown
        self.data_250146f: int = 0
    def encodeStruct(self):
        pass
    def decodeStruct(self, data):
        pass
    def decode(self, data_0000: bytes, data_0600: bytes, data_1280: bytes, data_1400: bytes):
        # Power-on
        self.poweron_interface = int(data_0000[0x6])
        self.poweron_display_1 = bytearray(data_0600[0x0:0xe])
        self.poweron_display_2 = bytearray(data_0600[0x10:0x1e])
        self.poweron_password = int(data_0000[0x7])
        self.poweron_password_char = data_0600[0x20:0x28].decode('utf-8').rstrip('\00')
        self.default_startup_channel = int(data_0000[0xd7])
        self.startup_zone_a = int(data_0000[0xd8])
        self.startup_channel_a = int(data_0000[0xda])
        self.startup_zone_b = int(data_0000[0xd9])
        self.startup_channel_b = int(data_0000[0xdb])
        self.startup_gps_test = int(data_0000[0xeb])
        self.startup_reset = int(data_0000[0xec])
        # Power Save
        self.auto_shutdown = int(data_0000[0x3])
        self.power_save = int(data_0000[0xb])
        self.auto_shutdown_type = int(data_1400[0x3f])
        # Display
        self.brightness = int(data_0000[0x26])
        self.auto_backlight_duration = int(data_0000[0x27])
        self.backlight_tx_delay = int(data_0000[0xe1])
        self.menu_exit_time = int(data_0000[0x37])
        self.time_display = int(data_0000[0x51])
        self.last_caller = int(data_0000[0x4d])
        self.call_display_mode = int(data_0000[0xaf])
        self.callsign_display_color = int(data_0000[0xbc])
        self.call_end_prompt_box = int(data_0000[0x3a])
        self.display_channel_number = int(data_0000[0xb8])
        self.display_current_contact = int(data_0000[0xb9])
        self.standby_char_color = int(data_0000[0xc0])
        self.standby_bk_picture = int(data_0000[0xc1])
        self.show_last_call_on_launch = int(data_0000[0xc2])
        self.separate_display = int(data_0000[0xe2])
        self.ch_switching_keeps_caller = int(data_0000[0xe3])
        self.backlight_rx_delay = int(data_0000[0xe6])
        self.channel_name_color_a = int(data_0000[0xe4])
        self.channel_name_color_b = int(data_1400[0x39])
        self.zone_name_color_a = int(data_1400[0x3d])
        self.zone_name_color_b = int(data_1400[0x3e])
        self.display_channel_type = Bit.getBit(data_1400[0x40], 0)
        self.display_time_slot = Bit.getBit(data_1400[0x40], 1)
        self.display_color_code = Bit.getBit(data_1400[0x40], 2)
        self.date_display_format = int(data_1400[0x42])
        self.volume_bar = int(data_0000[0x47])
        # Work Mode
        self.display_mode = int(data_0000[0x01])
        self.vf_mr_a = int(data_0000[0x15])
        self.vf_mr_b = int(data_0000[0x16])
        self.mem_zone_a = int(data_0000[0x1f])
        self.mem_zone_b = int(data_0000[0x20])
        self.main_channel_set = int(data_0000[0x2c])
        self.sub_channel_mode = int(data_0000[0x2d])
        self.working_mode = int(data_0000[0x34])
        # Vox/BT
        self.vox_level = int(data_0000[0x0c])
        self.vox_delay = int(data_0000[0x0d])
        self.vox_detection = int(data_0000[0x33])
        self.bt_on_off = int(data_0000[0xb1])
        self.bt_int_mic = int(data_0000[0xb2])
        self.bt_int_spk = int(data_0000[0xb3])
        self.bt_mic_gain = int(data_0000[0xb6])
        self.bt_spk_gain = int(data_0000[0xb7])
        self.bt_hold_time = int(data_0000[0xed])
        self.bt_rx_delay = int(data_0000[0xee])
        self.bt_ptt_hold = int(data_1400[0x21])
        self.bt_ptt_sleep_time = int(data_1400[0x34])
        # STE
        self.ste_type_of_ctcss = int(data_0000[0x17])
        self.ste_when_no_signal = int(data_0000[0x18])
        self.ste_time = int(data_1400[0x36])
        # FM
        self.fm_vfo_mem = int(data_0000[0x1e])
        self.fm_work_channel = int(data_0000[0x1d])
        self.fm_monitor = int(data_0000[0x2b])
        # Key Function
        self.key_lock = int(data_0000[0x02])
        self.pf1_short_key = int(data_0000[0x10])
        self.pf2_short_key = int(data_0000[0x11])
        self.pf3_short_key = int(data_0000[0x12])
        self.p1_short_key = int(data_0000[0x13])
        self.p2_short_key = int(data_0000[0x14])
        self.pf1_long_key = int(data_0000[0x41])
        self.pf2_long_key = int(data_0000[0x42])
        self.pf3_long_key = int(data_0000[0x43])
        self.p1_long_key = int(data_0000[0x44])
        self.p2_long_key = int(data_0000[0x45])
        self.long_key_time = int(data_0000[0x46])
        self.knob_lock = Bit.getBit(data_0000[0xbe], 0)
        self.keyboard_lock = Bit.getBit(data_0000[0xbe], 1)
        self.side_key_lock = Bit.getBit(data_0000[0xbe], 3)
        self.forced_key_lock = Bit.getBit(data_0000[0xbe], 4)
        # Other
        self.address_book_sent_with_code = int(data_0000[0xd5])
        self.tot = int(data_0000[0x04])
        self.language = int(data_0000[0x05])
        self.frequency_step = int(data_0000[0x08])
        self.sql_level_a = int(data_0000[0x09])
        self.sql_level_b = int(data_0000[0x0a])
        self.tbst = int(data_0000[0x2e])
        self.analog_call_hold_time = int(data_0000[0x50])
        self.call_channel_maintained = int(data_0000[0x6e])
        self.priority_zone_a = int(data_0000[0x6f])
        self.priority_zone_b = int(data_0000[0x70])
        self.mute_timing = int(data_0000[0xe9])
        self.encryption_type = int(data_1400[0x3a])
        self.tot_predict = int(data_1400[0x3b])
        self.tx_power_agc = int(data_1400[0x3c])
        self.priority_zone_a = self.priority_zone_a + 1 if self.priority_zone_a < 255 else 0
        self.priority_zone_b = self.priority_zone_b + 1 if self.priority_zone_b < 255 else 0
        # Digital Func
        self.group_call_hold_time = int(data_0000[0x19])
        self.private_call_hold_time = int(data_0000[0x1a])
        self.manual_dial_group_call_hold_time = int(data_1400[0x37])
        self.manual_dial_private_call_hold_time = int(data_1400[0x38])
        self.voice_header_repetitions = int(data_1400[0x6e])
        self.tx_preamble_duration = int(data_0000[0x1c])
        self.filter_own_id = int(data_0000[0x38])
        self.digital_remote_kill = int(data_0000[0x3c])
        self.digital_monitor = int(data_0000[0x49])
        self.digital_monitor_cc = int(data_0000[0x4a])
        self.digital_monitor_id = int(data_0000[0x4b])
        self.monitor_slot_hold = int(data_0000[0x4c])
        self.remote_monitor = int(data_0000[0x3e])
        self.sms_format = int(data_0000[0xc3])
        # Alert Tone
        self.sms_alert = int(data_0000[0x29])
        self.call_alert = int(data_0000[0x2f])
        self.digi_call_reset_tone = int(data_0000[0x32])
        self.talk_permit = int(data_0000[0x31])
        self.key_tone = int(data_0000[0x00])
        self.digi_idle_channel_tone = int(data_0000[0x36])
        self.startup_sound = int(data_0000[0x39])
        self.tone_key_sound_adjustable = int(data_0000[0xbb])
        self.analog_idle_channel_tone = int(data_1400[0x41])
        self.plugin_recording_tone = int(data_0000[0xb4])
        self.call_permit_first_tone_freq = int.from_bytes(data_0000[0x72:0x74], 'little')
        self.call_permit_first_tone_period = int.from_bytes(data_0000[0x7c:0x7e], 'little')
        self.call_permit_second_tone_freq = int.from_bytes(data_0000[0x74:0x76], 'little')
        self.call_permit_second_tone_period = int.from_bytes(data_0000[0x7e:0x80], 'little')
        self.call_permit_third_tone_freq = int.from_bytes(data_0000[0x76:0x78], 'little')
        self.call_permit_third_tone_period = int.from_bytes(data_0000[0x80:0x82], 'little')
        self.call_permit_fourth_tone_freq = int.from_bytes(data_0000[0x78:0x7a], 'little')
        self.call_permit_fourth_tone_period = int.from_bytes(data_0000[0x82:0x84], 'little')
        self.call_permit_fifth_tone_freq = int.from_bytes(data_0000[0x7a:0x7c], 'little')
        self.call_permit_fifth_tone_period = int.from_bytes(data_0000[0x84:0x86], 'little')
        self.idle_channel_first_tone_freq = int.from_bytes(data_0000[0x86:0x88], 'little')
        self.idle_channel_first_tone_period = int.from_bytes(data_0000[0x90:0x92], 'little')
        self.idle_channel_second_tone_freq = int.from_bytes(data_0000[0x88:0x8a], 'little')
        self.idle_channel_second_tone_period = int.from_bytes(data_0000[0x92:0x94], 'little')
        self.idle_channel_third_tone_freq = int.from_bytes(data_0000[0x8a:0x8c], 'little')
        self.idle_channel_third_tone_period = int.from_bytes(data_0000[0x94:0x96], 'little')
        self.idle_channel_fourth_tone_freq = int.from_bytes(data_0000[0x8c:0x8e], 'little')
        self.idle_channel_fourth_tone_period = int.from_bytes(data_0000[0x96:0x98], 'little')
        self.idle_channel_fifth_tone_freq = int.from_bytes(data_0000[0x8e:0x90], 'little')
        self.idle_channel_fifth_tone_period = int.from_bytes(data_0000[0x98:0x9a], 'little')
        self.call_reset_first_tone_freq = int.from_bytes(data_0000[0x9a:0x9c], 'little')
        self.call_reset_first_tone_period = int.from_bytes(data_0000[0xa4:0xa6], 'little')
        self.call_reset_second_tone_freq = int.from_bytes(data_0000[0x9c:0x9e], 'little')
        self.call_reset_second_tone_period = int.from_bytes(data_0000[0xa6:0xa8], 'little')
        self.call_reset_third_tone_freq = int.from_bytes(data_0000[0x9e:0xa0], 'little')
        self.call_reset_third_tone_period = int.from_bytes(data_0000[0xa8:0xaa], 'little')
        self.call_reset_fourth_tone_freq = int.from_bytes(data_0000[0xa0:0xa2], 'little')
        self.call_reset_fourth_tone_period = int.from_bytes(data_0000[0xaa:0xac], 'little')
        self.call_reset_fifth_tone_freq = int.from_bytes(data_0000[0xa2:0xa4], 'little')
        self.call_reset_fifth_tone_period = int.from_bytes(data_0000[0xac:0xae], 'little')
        # Alert Tone 1
        self.call_end_first_tone_freq = int.from_bytes(data_1400[0x46:0x48], 'little')
        self.call_end_first_tone_period = int.from_bytes(data_1400[0x50:0x52], 'little')
        self.call_end_second_tone_freq = int.from_bytes(data_1400[0x48:0x4a], 'little')
        self.call_end_second_tone_period = int.from_bytes(data_1400[0x52:0x54], 'little')
        self.call_end_third_tone_freq = int.from_bytes(data_1400[0x4a:0x4c], 'little')
        self.call_end_third_tone_period = int.from_bytes(data_1400[0x54:0x56], 'little')
        self.call_end_fourth_tone_freq = int.from_bytes(data_1400[0x4c:0x4e], 'little')
        self.call_end_fourth_tone_period = int.from_bytes(data_1400[0x56:0x58], 'little')
        self.call_end_fifth_tone_freq = int.from_bytes(data_1400[0x4e:0x50], 'little')
        self.call_end_fifth_tone_period = int.from_bytes(data_1400[0x58:0x5a], 'little')
        self.call_all_first_tone_freq = int.from_bytes(data_1400[0x5a:0x5c], 'little')
        self.call_all_first_tone_period = int.from_bytes(data_1400[0x64:0x66], 'little')
        self.call_all_second_tone_freq = int.from_bytes(data_1400[0x5c:0x5e], 'little')
        self.call_all_second_tone_period = int.from_bytes(data_1400[0x66:0x68], 'little')
        self.call_all_third_tone_freq = int.from_bytes(data_1400[0x5e:0x60], 'little')
        self.call_all_third_tone_period = int.from_bytes(data_1400[0x68:0x6a], 'little')
        self.call_all_fourth_tone_freq = int.from_bytes(data_1400[0x60:0x62], 'little')
        self.call_all_fourth_tone_period = int.from_bytes(data_1400[0x6a:0x6c], 'little')
        self.call_all_fifth_tone_freq = int.from_bytes(data_1400[0x62:0x64], 'little')
        self.call_all_fifth_tone_period = int.from_bytes(data_1400[0x6c:0x6e], 'little')
        # GPS/Ranging
        self.gps_power = int(data_0000[0x28])
        self.gps_positioning = int(data_0000[0x3f])
        self.time_zone = int(data_0000[0x30])
        self.ranging_interval = int(data_0000[0xb5])
        self.distance_unit = int(data_0000[0xbd])
        self.gps_template_information = int(data_0000[0x53])
        self.gps_information_char = data_1280[0x0:0x20].decode('utf-8').rstrip('\x00')
        self.gps_mode = int(data_1400[0x35])
        # self.gps_roaming = int(data_0000[0x])
        # VFO Scan
        self.vfo_scan_type = int(data_0000[0x0e])
        self.vfo_scan_start_freq_uhf = int.from_bytes(data_0000[0x58:0x5c], 'little')
        self.vfo_scan_end_freq_uhf = int.from_bytes(data_0000[0x5c:0x60], 'little')
        self.vfo_scan_start_freq_vhf = int.from_bytes(data_0000[0x60:0x64], 'little')
        self.vfo_scan_end_freq_vhf = int.from_bytes(data_0000[0x64:0x68], 'little')
        # Auto Repeater
        self.auto_repeater_a = int(data_0000[0x48])
        self.auto_repeater_b = int(data_0000[0xd4])
        self.auto_repeater_1_uhf = int(data_0000[0x68])
        self.auto_repeater_1_vhf = int(data_0000[0x69])
        self.auto_repeater_2_uhf = int(data_1400[0x22])
        self.auto_repeater_2_vhf = int(data_1400[0x23])
        self.repeater_check = int(data_0000[0xdd])
        self.repeater_check_interval = int(data_0000[0xde])
        self.repeater_check_reconnections = int(data_0000[0xdf])
        self.repeater_out_of_range_notify = int(data_0000[0xe5])
        self.out_of_range_notify = int(data_0000[0xea])
        self.auto_roaming = int(data_0000[0xe7])
        self.auto_roaming_start_condition = int(data_0000[0xe0])
        self.auto_roaming_fixed_time = int(data_0000[0xba])
        self.roaming_effect_wait_time = int(data_0000[0xbf])
        self.roaming_zone = int(data_0000[0xd5])
        self.auto_repeater_1_min_freq_vhf = int.from_bytes(data_0000[0xc4:0xc8], 'little')
        self.auto_repeater_1_max_freq_vhf = int.from_bytes(data_0000[0xc8:0xcc], 'little')
        self.auto_repeater_1_min_freq_uhf = int.from_bytes(data_0000[0xcc:0xd0], 'little')
        self.auto_repeater_1_max_freq_uhf = int.from_bytes(data_0000[0xd0:0xd4], 'little')
        self.auto_repeater_2_min_freq_vhf = int.from_bytes(data_1400[0x24:0x28], 'little')
        self.auto_repeater_2_max_freq_vhf = int.from_bytes(data_1400[0x28:0x2c], 'little')
        self.auto_repeater_2_min_freq_uhf = int.from_bytes(data_1400[0x2c:0x30], 'little')
        self.auto_repeater_2_max_freq_uhf = int.from_bytes(data_1400[0x30:0x34], 'little')
        # Record
        self.record_function = int(data_0000[0x22])
        # Volume/Audio
        self.max_volume = int(data_0000[0x3b])
        self.max_headphone_volume = int(data_0000[0x52])
        self.digi_mic_gain = int(data_0000[0x0f])
        self.enhanced_sound_quality = int(data_0000[0x57])
        self.analog_mic_gain = int(data_1400[0x43])
        # Unknown
        self.data_250146f = data_1400[0x6f]
class PrefabricatedSMS:
    struct_format = '<'
    def __init__(self):
        self.id: int = 0
        self.text: str = ''
    def encodeStruct(self):
        pass
    def decodeStruct(self, data):
        pass
    def encode(self) -> bytes:
        data = self.text.encode('utf-8').ljust(0xd0, b'\x00')
        return data
    def decode(self, data: bytes):
        self.text = data.decode('utf-8').rstrip('\x00')
class RadioID:
    struct_format = '<BI9s'
    def __init__(self):
        self.id: int = 0
        self.dmr_id: int = 0
        self.name: str = ''
    def encodeStruct(self):
        data = struct.pack(self.struct_format,
            self.id,
            self.dmr_id,
            self.name.encode('utf-8')
        )
        return data
    def decodeStruct(self, data):
        fdata = struct.unpack(self.struct_format, data)
        self.id = fdata[0]
        self.dmr_id = fdata[1]
        self.name = fdata[2].decode('utf-8').rstrip('\x00')
    def decode(self, data: bytes):
        self.dmr_id = int(data[:4].hex())
        self.name = data[5:0x1f].decode('utf-8').rstrip('\x00')
    def encode(self) -> bytes:
        data = bytearray(0x20)
        data[0:4] = bytearray(bytes.fromhex(str(self.dmr_id).rjust(8,'0')))
        data[5:0x1f] = self.name.encode('utf-8').ljust(26, b'\x00')
        return bytes(data)
class ReceiveGroupCallList:
    def __init__(self):
        self.id: int = 0
        self.name: str = ''
        self.talkgroups: list[TalkGroup] = []
        self.temp_tg_names = []
        self.temp_tg_ids = []
class RoamingChannel:
    struct_format = '<'
    def __init__(self):
        self.id: int = 0
        self.rx_frequency: int = 0
        self.tx_frequency: int = 0
        self.name: str = ''
        self.color_code: int = 0
        self.slot: int = 0
    def getRxFrequencyDecimal(self) -> Decimal:
        return Decimal(self.rx_frequency) / 100000
    def getRxFrequencyStr(self):
        return format(f'{self.getRxFrequencyDecimal():.5f}')
    def getTxFrequencyDecimal(self) -> Decimal:
        return Decimal(self.tx_frequency) / 100000
    def getTxFrequencyStr(self):
        return format(f'{self.getTxFrequencyDecimal():.5f}')
    def encodeStruct(self):
        pass
    def decodeStruct(self, data: bytes):
        pass
    def encode(self) -> bytes:
        data = bytearray(0x20)
        data[0:4] = bytearray(bytes.fromhex(str(self.rx_frequency).rjust(8,'0')))
        data[4:8] = bytearray(bytes.fromhex(str(self.tx_frequency).rjust(8,'0')))
        data[0x8] = self.color_code
        data[0x9] = self.slot
        data[0xa:0x1a] = self.name.encode('utf-8').ljust(16, b'\x00')
        return bytes(data)
    def decode(self, data: bytes):
        self.rx_frequency = int(data[0:4].hex())
        self.tx_frequency = int(data[4:8].hex())
        self.color_code = data[0x8]
        self.slot = data[0x9]
        self.name = data[0xa:0x1a].decode('utf-8').rstrip('\x00')
class RoamingZone:
    struct_format = '<'
    def __init__(self):
        self.id: int = 0
        self.name: str = ''
        self.roaming_channels: list[RoamingChannel] = []
        self.temp_roaming_channels = []
    def encodeStruct(self):
        pass
    def decodeStruct(self, data: bytes):
        pass
    def encode(self) -> bytes:
        data = bytearray([0xff]) * 0x50
        data[0x40:0x50] = self.name.encode('utf-8').ljust(16, b'\x00')
        for i, rc in enumerate(self.roaming_channels):
            if rc.rx_frequency > 0:
                data[i] = rc.id
        return bytes(data)
    def decode(self, data: bytes):
        self.name = data[0x40:0x50].decode('utf-8').rstrip('\x00')
        for ch_idx in data[0:0x40]:
            if ch_idx == 0xff:
                break
            self.temp_roaming_channels.append(ch_idx)
class ScanList:
    struct_format = '<B16sBBHHBBBBBH'
    def __init__(self):
        self.id: int = -1
        self.name: str = ''
        self.channels: list[Channel] = []
        self.scan_mode: int = 0
        self.priority_channel_select: int = 0
        self.priority_channel_1: int = 0xffff
        self.priority_channel_2: int = 0xffff
        self.revert_channel: int = 0
        self.look_back_time_a: int = 0
        self.look_back_time_b: int = 0
        self.dropout_delay_time: int = 0
        self.dwell_time: int = 0
        self.temp_member_channels = []
        self.temp_priority_1 = 0
        self.temp_priority_2 = 0
    def activeChannels(self):
        ch_list = []
        for ch in self.channels:
            if ch.rx_frequency != 0:
                ch_list.append(ch)
        return ch_list
    def clear(self):
        self.name = ''
        self.scan_mode = 0
        self.priority_channel_select = 0
        self.priority_channel_1 = 0xffff
        self.priority_channel_2 = 0xffff
        self.revert_channel = 0
        self.look_back_time_a = 0
        self.look_back_time_b = 0
        self.dropout_delay_time = 0
        self.dwell_time = 0
        self.channel_count = 0
        self.temp_member_channels = []
        self.temp_priority_1 = 0
        self.temp_priority_2 = 0
        self.channels.clear()
    def encodeStruct(self):
        data = b''
        data = struct.pack(self.struct_format,
            self.id,
            self.name.encode('utf-8'),
            self.scan_mode,
            self.priority_channel_select,
            self.priority_channel_1,
            self.priority_channel_2,
            self.revert_channel,
            self.look_back_time_a,
            self.look_back_time_b,
            self.dropout_delay_time,
            self.dwell_time,
            len(self.channels))
        for ch in self.channels:
            data += struct.pack('<H', ch.id)
        return data
    def decodeStruct(self, data):
        fdata = struct.unpack(self.struct_format, data)
        self.id = fdata[0]
        self.name = fdata[1].decode('utf-8').rstrip('\x00')
        self.scan_mode = fdata[2]
        self.priority_channel_select = fdata[3]
        self.temp_priority_1 = fdata[4]
        self.temp_priority_2 = fdata[5]
        self.revert_channel = fdata[6]
        self.look_back_time_a = fdata[7]
        self.look_back_time_b = fdata[8]
        self.dropout_delay_time = fdata[9]
        self.dwell_time = fdata[10]
        self.channel_count = fdata[11]
    def decode(self, data: bytes):
        self.priority_channel_select = int(data[0x1])
        self.priority_channel_1 = int.from_bytes(data[0x2:0x4], 'little')
        self.priority_channel_2 = int.from_bytes(data[0x4:0x6], 'little')
        self.look_back_time_a = int.from_bytes(data[0x6:0x8], 'little') - 5
        self.look_back_time_b = int.from_bytes(data[0x8:0xa], 'little') - 5
        self.dropout_delay_time = int.from_bytes(data[0xa:0xc], 'little') - 1
        self.dwell_time = int.from_bytes(data[0xc:0xe], 'little') - 1
        self.revert_channel = int.from_bytes(data[0xe:0xf], 'little')
        self.name = data[0xf:0x1f].decode('utf-8').rstrip('\00')
        self.temp_member_channels.clear()
        for i in range(0, 100, 2):
            ch_idx = int.from_bytes(data[0x1f + i: 0x1f + i + 2], 'big')
            if ch_idx != 0xffff:
                self.temp_member_channels.append(ch_idx)
    def encode(self) -> bytes:
        data = bytearray(0x1e)
        data[0x1] = self.priority_channel_select
        data[0x2:0x4] = self.priority_channel_1.to_bytes(2, 'little')
        data[0x4:0x6] = self.priority_channel_2.to_bytes(2, 'little')
        data[0x6:0x8] = (self.look_back_time_a + 5).to_bytes(2, 'little')
        data[0x8:0xa] = (self.look_back_time_b + 5).to_bytes(2, 'little')
        data[0xa:0xc] = (self.dropout_delay_time + 1).to_bytes(2, 'little')
        data[0xc:0xe] = (self.dwell_time + 1).to_bytes(2, 'little')
        data[0xe:0xf] = (self.revert_channel).to_bytes(2, 'little')
        data[0xf:0x1f] = self.name.encode('utf-8').ljust(0x10, b'\x00')
        channel_data = bytearray([0xff]) * 0x65
        for i, ch in enumerate(self.channels):
            if i < 100:
                channel_data[(i*2):(i*2) + 2] = ch.id.to_bytes(2, 'big')
        data += channel_data + bytearray(0xc)
        return data
class TalkAliasSettings:
    struct_format = ''
    def __init__(self):
        pass
    def encodeStruct(self) -> bytes:
        pass
    def decodeStruct(self, data:bytes):
        pass
    def encode(self) -> bytes:
        pass
    def decode(self, data:bytes):
        pass
class TalkGroup:
    struct_format = '<HIB16sB'
    def __init__(self, primary_data : bytes = None, secondary_data : bytes = None):
        self.id: int = 0xff
        self.tg_dmr_id: int = 0
        self.call_alert: int = 0
        self.name: str = ''
        self.call_type: int = 0
    def encodeStruct(self):
        data = struct.pack(self.struct_format,
            self.id,
            self.tg_dmr_id,
            self.call_alert,
            self.name.encode('utf-8'),
            self.call_type
        )
        return data
    def decodeStruct(self, data):
        fdata = struct.unpack(self.struct_format, data)
        self.id = fdata[0]
        self.tg_dmr_id = fdata[1]
        self.call_alert = fdata[2]
        self.name = fdata[3].decode('utf-8').rstrip('\x00')
        self.call_type = fdata[4]
    def decode(self, data: bytes):
        self.call_type = int(data[0])
        self.name = data[0x1:0x11].decode('utf-8').rstrip('\x00')
        self.call_alert = int(data[0x22])
        self.tg_dmr_id = int.from_bytes(data[0x23:0x27], 'big')
    def encode(self) -> bytes:
        data = bytearray(0x64)
        data[0] = self.call_type
        data[0x1:0x11] = self.name.encode('utf-8').ljust(0x10, b'\x00')
        data[0x22] = self.call_alert
        data[0x23:0x27] = self.tg_dmr_id.to_bytes(4, 'big')
        return data
class Tone2FrequencyDecodeItem:
    struct_format = ''
    def __init__(self):
        pass
    def encodeStruct(self) -> bytes:
        pass
    def decodeStruct(self, data:bytes):
        pass
    def encode(self) -> bytes:
        pass
    def decode(self, data:bytes):
        pass
class Tone2FrequencyEncodeItem:
    struct_format = ''
    def __init__(self):
        pass
    def encodeStruct(self) -> bytes:
        pass
    def decodeStruct(self, data:bytes):
        pass
    def encode(self) -> bytes:
        pass
    def decode(self, data:bytes):
        pass
class Tone2Settings:
    struct_format = ''
    def __init__(self):
        pass
    def encodeStruct(self) -> bytes:
        pass
    def decodeStruct(self, data:bytes):
        pass
    def encode(self) -> bytes:
        pass
    def decode(self, data:bytes):
        pass
class Tone5EncodeItem:
    struct_format = ''
    def __init__(self):
        pass
    def encodeStruct(self) -> bytes:
        pass
    def decodeStruct(self, data:bytes):
        pass
    def encode(self) -> bytes:
        pass
    def decode(self, data:bytes):
        pass
class Tone5Settings:
    struct_format = ''
    def __init__(self):
        pass
    def encodeStruct(self) -> bytes:
        pass
    def decodeStruct(self, data:bytes):
        pass
    def encode(self) -> bytes:
        pass
    def decode(self, data:bytes):
        pass
class Zone:
    struct_format = '<B16s?3I'
    def __init__(self):
        self.id : int = 0xff
        self.name : str = ''
        self.hide: bool = False
        self.a_channel : int = 0
        self.b_channel : int = 0
        self.channels: list[Channel] = []
        self.channel_count: int = 0
        self.a_channel_obj: Channel = None
        self.b_channel_obj: Channel = None
        self.temp_member_channels = []
    def clear(self):
        self.id : int = 0xff
        self.name : str = ''
        self.hide: bool = False
        self.a_channel : int = 0
        self.b_channel : int = 0
        self.channel_count: int = 0
        self.channels.clear()
        self.a_channel_obj = None
        self.b_channel_obj = None
        self.temp_member_channels = []
        self.temp_member_idx = []
    def encodeStruct(self):
        data = b''
        data += struct.pack(self.struct_format,
                            self.id,
                            self.name.encode('utf-8'),
                            self.hide,
                            self.a_channel,
                            self.b_channel,
                            len(self.channels))
        for ch in self.channels:
            data += struct.pack('<H', ch.id)
        return data
    def decodeStruct(self, data):
        fdata = struct.unpack(self.struct_format, data)
        self.id = fdata[0]
        self.name = fdata[1].decode('utf-8').rstrip('\x00')
        self.hide = fdata[2]
        self.a_channel = fdata[3]
        self.b_channel = fdata[4]
        self.channel_count = fdata[5]
    # Because of the way zones are in memory, they are decoded in DeviceSerial
class AnyToneMemorySignals(QObject):
    finished = Signal()
    update1 = Signal(int, int, str)
    update2 = Signal(int, int, str)
class AnyToneMemory:
    radio_data = b''
    fw_data = b''
    radio_mode = 0
    channels: list[Channel] = []
    zones: list[Zone] = []
    talkgroups: list[TalkGroup] = []
    radioid_list: list[RadioID] = []
    scanlist: list[ScanList] = []
    optional_settings: OptionalSettings = None
    master_radioid: MasterRadioId = MasterRadioId()
    receive_group_call_lists: list[ReceiveGroupCallList] = []
    roaming_channels: list[RoamingChannel] = []
    roaming_zones: list[RoamingZone] = []
    fm_channels: list[FM] = []
    digital_contact_list: list[DigitalContact] = []
    prefabricated_sms_list: list[PrefabricatedSMS] = []
    auto_repeater_freq_list: list[AutoRepeaterOffsetFrequency] = []
    gps_roaming_list: list[GpsRoaming] = []
    alarm_settings: AlarmSettings = None
    aes_encryption_keys: list[AesEncryptionCode] = []
    # Device Information
    radio_model: str = 'D878UVII'
    radio_band: str = 'UHF{400 - 480 MHz}\nVHF{136 - 174 MHz}'
    radio_version: str = 'V1.01'
    signals: AnyToneMemorySignals = None
    def init():
        AnyToneMemory.initChannels()
        AnyToneMemory.initZones()
        AnyToneMemory.initTalkgroups()
        AnyToneMemory.initRadioIdList()
        AnyToneMemory.initScanLists()
        AnyToneMemory.initReceiveCallGroupLists()
        AnyToneMemory.initRoamingChannels()
        AnyToneMemory.initRoamingZones()
        AnyToneMemory.initFM()
        AnyToneMemory.initDigitalContactList()
        AnyToneMemory.initOptionalSettings()
        AnyToneMemory.iniPrefabricatedSMS()
        AnyToneMemory.initAutoRepeaterOffsetFrequencies()
        AnyToneMemory.initGpsRoaming()
        AnyToneMemory.initAlarmSettings()
        AnyToneMemory.initAesEncryptionKeys()
        AnyToneMemory.setDefaults()
    def initChannels():
        AnyToneMemory.channels.clear()
        for i in range(4002):
            ch = Channel()
            ch.id = i
            AnyToneMemory.channels.append(ch)
    def initZones():
        AnyToneMemory.zones.clear()
        for i in range(250):
            zone = Zone()
            zone.id = i
            AnyToneMemory.zones.append(zone)
    def initTalkgroups():
        AnyToneMemory.talkgroups.clear()
        for i in range(10000):
            tg = TalkGroup()
            tg.id = i
            AnyToneMemory.talkgroups.append(tg)
    def initRadioIdList():
        AnyToneMemory.radioid_list.clear()
        for i in range(250):
            rid = RadioID()
            rid.id = i
            AnyToneMemory.radioid_list.append(rid)
    def initScanLists():
        AnyToneMemory.scanlist.clear()
        for i in range(250):
            sl = ScanList()
            sl.id = i
            AnyToneMemory.scanlist.append(sl)
    def initReceiveCallGroupLists():
        AnyToneMemory.receive_group_call_lists.clear()
        for i in range(100):
            rgcl = ReceiveGroupCallList()
            rgcl.id = i
            AnyToneMemory.receive_group_call_lists.append(rgcl)
    def initRoamingChannels():
        AnyToneMemory.roaming_channels.clear()
        for i in range(250):
            rc = RoamingChannel()
            rc.id = i
            AnyToneMemory.roaming_channels.append(rc)
    def initRoamingZones():
        AnyToneMemory.roaming_zones.clear()
        for i in range(64):
            rz = RoamingZone()
            rz.id = i
            AnyToneMemory.roaming_zones.append(rz)
    def initFM():
        AnyToneMemory.fm_channels.clear()
        for i in range(101):
            fm = FM()
            fm.id = i
            AnyToneMemory.fm_channels.append(fm)
    def initDigitalContactList():
        AnyToneMemory.digital_contact_list.clear()
        for i in range(500000):
            dc = DigitalContact()
            dc.id = i
            AnyToneMemory.digital_contact_list.append(dc)
    def initOptionalSettings():
        AnyToneMemory.optional_settings = OptionalSettings()
    def iniPrefabricatedSMS():
        AnyToneMemory.prefabricated_sms_list.clear()
        for i in range(100):
            sms = PrefabricatedSMS()
            sms.id = i
            AnyToneMemory.prefabricated_sms_list.append(sms)
    def initAutoRepeaterOffsetFrequencies():
        AnyToneMemory.auto_repeater_freq_list.clear()
        for i in range(250):
            sms = AutoRepeaterOffsetFrequency()
            sms.id = i
            AnyToneMemory.auto_repeater_freq_list.append(sms)
    def initGpsRoaming():
        AnyToneMemory.gps_roaming_list.clear()
        for i in range(32):
            gps = GpsRoaming()
            gps.id = i
            AnyToneMemory.gps_roaming_list.append(gps)
    def initAlarmSettings():
        AnyToneMemory.alarm_settings = AlarmSettings()
    def initAesEncryptionKeys():
        AnyToneMemory.aes_encryption_keys.clear()
        for i in range(255):
            key = AesEncryptionCode()
            key.index = i
            AnyToneMemory.aes_encryption_keys.append(key)
    def setDefaults():
        # TODO
        # Common
        AnyToneMemory.setDefaultChannels()
        # Digital
        AnyToneMemory.setDefaultMasterID()
        # Analog
    def setDefaultChannels():
        pass
    def setDefaultMasterID():
        AnyToneMemory.master_radioid.dmr_id = 12345678
        AnyToneMemory.master_radioid.name = 'My Radio'
        AnyToneMemory.master_radioid.used = False
    def findChannel(name: str, rx_frequency: int, tx_frequency = None):
        for ch in AnyToneMemory().channels:
            if ch.rx_frequency != 0:
                ch_tx = ch.rx_frequency
                if ch.offset_direction == 1:
                    ch_tx = ch.rx_frequency + ch.offset
                elif ch.offset_direction == 2:
                    ch_tx = ch.rx_frequency - ch.offset
                if ch.name == name and ch.rx_frequency == rx_frequency and (tx_frequency == None or ch_tx == tx_frequency):
                    return ch
        return None
    def linkReferences():
        AnyToneMemory.linkChannelData()
        AnyToneMemory.linkScanListChannels()
        AnyToneMemory.linkZoneChannels()
        AnyToneMemory.linkReceiveGroupCall()
        AnyToneMemory.linkRoamingZoneChannels()
    def linkZoneChannels():
        steps = len(AnyToneMemory.zones)
        for i, zone in enumerate(AnyToneMemory.zones):
            if AnyToneMemory.signals != None:
                    AnyToneMemory.signals.update2.emit(i, steps, "Linking Zone Channels")
            zone.channels.clear()
            if len(zone.channels) != 0 or len(zone.temp_member_channels) != 0:
                for ch_idx in zone.temp_member_channels:
                    ch: Channel = AnyToneMemory.channels[ch_idx]
                    if ch != None:
                        zone.channels.append(ch)
                zone.a_channel_obj = zone.channels[zone.a_channel]
                zone.b_channel_obj = zone.channels[zone.b_channel]
                # ch: Channel = AnyToneMemory.findChannel(zone.temp_member_b[0], zone.temp_member_b[1], zone.temp_member_b[2])
                # if ch != None:
                #     zone.b_channel_obj = ch
                zone.channel_count = len(zone.channels)
        if AnyToneMemory.signals != None:
            AnyToneMemory.signals.update2.emit(steps, steps, "Linking Zone Channels")
    def linkChannelData():
        steps = len(AnyToneMemory.channels)
        for i, ch in enumerate(AnyToneMemory.channels):
            if AnyToneMemory.signals != None:
                AnyToneMemory.signals.update2.emit(i, steps, "Linking Channels Data")
            if ch.rx_frequency != 0:
                # TalkGroup
                if ch.temp_talkgroup[0] != '':
                    for i, tg in enumerate(AnyToneMemory.talkgroups):
                        if tg.name == ch.temp_talkgroup[0] and tg.tg_dmr_id == ch.temp_talkgroup[1]:
                            ch.contact = i
                            ch.talkgroup_obj = tg
                    if ch.talkgroup_obj.tg_dmr_id == 0:
                        ch.talkgroup_obj = AnyToneMemory.talkgroups[0]
                else:
                    ch.talkgroup_obj = AnyToneMemory.talkgroups[ch.contact]
                # Radio ID
                if ch.temp_radio_id != '':
                    for i, rid in enumerate(AnyToneMemory.radioid_list):
                        if rid.name == ch.temp_radio_id:
                            ch.radio_id_idx = i
                            ch.radioid_obj = rid
                else:
                    ch.radioid_obj = AnyToneMemory.radioid_list[ch.radio_id_idx]
                # Scan List
                if ch.scan_list_name != None:
                    for i, sl in enumerate(AnyToneMemory.scanlist):
                        if sl.name == ch.scan_list_name:
                            ch.scan_list = sl
                if ch.scan_list_idx != 0xff:
                    ch.scan_list = AnyToneMemory.scanlist[ch.scan_list_idx]
                # Receive Group Call List
                if ch.receive_group_list_name != None:
                    for i, rgcl in enumerate(AnyToneMemory.receive_group_call_lists):
                        if rgcl.name == ch.receive_group_list_name:
                            ch.receive_group_list = rgcl
        if AnyToneMemory.signals != None:
            AnyToneMemory.signals.update2.emit(steps, steps, "Linking Channels Data")
    def linkScanListChannels():
        steps = len(AnyToneMemory.scanlist)
        for i, sl in enumerate(AnyToneMemory.scanlist):
            if AnyToneMemory.signals != None:
                    AnyToneMemory.signals.update2.emit(i, steps, "Linking Scan List Channels")
            sl.channels.clear()
            if len(sl.temp_member_channels) != 0:
                for ch_idx in sl.temp_member_channels:
                    ch: Channel = AnyToneMemory.channels[ch_idx]
                    if ch != None:
                        sl.channels.append(ch)
                    # for ch in AnyToneMemory.channels:
                    #     ch: Channel = ch
                    #     if ch.name == ch_data[0] and ch.rx_frequency == int(Decimal(ch_data[1]) * 100000):
                    #         sl.channels.append(ch)
                if sl.priority_channel_1 == -1:
                    sl.priority_channel_1 = 0
                    for i, c in enumerate(sl.channels):
                        if c.name == sl.temp_priority_1[0] and c.rx_frequency == sl.temp_priority_1[1]:
                            sl.priority_channel_1 = i + 1
                if sl.priority_channel_2 == -1:
                    sl.priority_channel_2 = 0
                    for i, c in enumerate(sl.channels):
                        if c.name == sl.temp_priority_2[0] and c.rx_frequency == sl.temp_priority_2[1]:
                            sl.priority_channel_2 = i + 1
        if AnyToneMemory.signals != None:
            AnyToneMemory.signals.update2.emit(steps, steps, "Linking Scan List Channels")
    def linkReceiveGroupCall():
        for rgcl in AnyToneMemory.receive_group_call_lists:
            if len(rgcl.temp_tg_names) != 0:
                rgcl.talkgroups.clear()
                for i in range(len(rgcl.temp_tg_names)):
                    for tg in AnyToneMemory.talkgroups:
                        if tg.tg_dmr_id != 0:
                            if tg.name == rgcl.temp_tg_names[i] and tg.tg_dmr_id == int(rgcl.temp_tg_ids[i]):
                                rgcl.talkgroups.append(tg)
    def linkRoamingZoneChannels():
        for rz in AnyToneMemory.roaming_zones:
            if len(rz.temp_roaming_channels) != 0:
                rz.roaming_channels.clear()
                for i in range(len(rz.temp_roaming_channels)):
                    if isinstance(rz.temp_roaming_channels[i], int):
                        rz.roaming_channels.append(AnyToneMemory.roaming_channels[rz.temp_roaming_channels[i]])
                    else:
                        for rc in AnyToneMemory.roaming_channels:
                            if rc.name == rz.temp_roaming_channels[i]:
                                    rz.roaming_channels.append(rc)

class MemoryController(QObject):
    CHANNELS = 0
    RADIO_IDS = 1
    ZONES = 2
    SCANLISTS = 3
    ANALOG_ADDRESS_BOOK = 4
    TALKGROUPS = 5
    PREFAB_SMS = 6
    FM = 7
    RECEIVE_GROUPCALL_LIST = 8
    TONE5_ENCODE = 9
    TONE2_ENCODE = 10
    DTMF_ENCODE = 11
    HOTKEY_QUICKCALL = 12
    HOTKEY_STATE = 13
    HOTKEY_HOTKEY = 14
    DIGITAL_CONTACT_LIST = 15
    AUTO_REPEATER_OFFSET_FREQ = 16
    ROAMING_CHANNELS = 17
    ROAMING_ZONES = 18
    APRS = 19
    GPS_ROAMING = 20
    OPTIONAL_SETTINGS = 21
    ALERT_TONE = 22
    AES_ENCRYPTION_CODE = 23
    ARC4_ENCRYPTION_CODE = 24
    update1 = Signal(int, int, str)
    update2 = Signal(int, int, str)
    memory = AnyToneMemory()
    def __init__(self):
        super().__init__()

