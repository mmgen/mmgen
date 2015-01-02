#!/usr/bin/python

# Chdir to repo root.
# Since script is not in repo root, fix sys.path so that modules are
# imported from repo, not system.
import sys,os
pn = os.path.dirname(sys.argv[0])
os.chdir(os.path.join(pn,os.pardir))
sys.path.__setitem__(0,os.path.abspath(os.curdir))

hincog_fn = "rand_data"
non_mmgen_fn = "btckey"

from collections import OrderedDict
cmd_data = OrderedDict([
#     test               description                  depends
	['walletgen',       (1,'wallet generation',        [[[],1]])],
	['walletchk',       (1,'wallet check',             [[["mmdat"],1]])],
	['addrgen',         (1,'address generation',       [[["mmdat"],1]])],
	['addrimport',      (1,'address import',           [[["addrs"],1]])],
	['txcreate',        (1,'transaction creation',     [[["addrs"],1]])],
	['txsign',          (1,'transaction signing',      [[["mmdat","raw"],1]])],
	['txsend',          (1,'transaction sending',      [[["sig"],1]])],

	['export_seed',     (1,'seed export to mmseed format',   [[["mmdat"],1]])],
	['export_mnemonic', (1,'seed export to mmwords format',  [[["mmdat"],1]])],
	['export_incog',    (1,'seed export to mmincog format',  [[["mmdat"],1]])],
	['export_incog_hex',(1,'seed export to mmincog hex format', [[["mmdat"],1]])],
	['export_incog_hidden',(1,'seed export to hidden mmincog format', [[["mmdat"],1]])],

	['addrgen_seed',    (1,'address generation from mmseed file', [[["mmseed","addrs"],1]])],
	['addrgen_mnemonic',(1,'address generation from mmwords file',[[["mmwords","addrs"],1]])],
	['addrgen_incog',   (1,'address generation from mmincog file',[[["mmincog","addrs"],1]])],
	['addrgen_incog_hex',(1,'address generation from mmincog hex file',[[["mmincox","addrs"],1]])],
	['addrgen_incog_hidden',(1,'address generation from hidden mmincog file', [[[hincog_fn,"addrs"],1]])],

	['keyaddrgen',    (1,'key-address file generation', [[["mmdat"],1]])],
	['txsign_keyaddr',(1,'transaction signing with key-address file', [[["akeys.mmenc","raw"],1]])],

	['walletgen2',(2,'wallet generation (2)',     [])],
	['addrgen2',  (2,'address generation (2)',    [[["mmdat"],2]])],
	['txcreate2', (2,'transaction creation (2)',  [[["addrs"],2]])],
	['txsign2',   (2,'transaction signing, two transactions',[[["mmdat","raw"],1],[["mmdat","raw"],2]])],
	['export_mnemonic2', (2,'seed export to mmwords format (2)',[[["mmdat"],2]])],

	['walletgen3',(3,'wallet generation (3)',         [])],
	['addrgen3',  (3,'address generation (3)',        [[["mmdat"],3]])],
	['txcreate3', (3,'tx creation with inputs and outputs from two wallets', [[["addrs"],1],[["addrs"],3]])],
	['txsign3',   (3,'tx signing with inputs and outputs from two wallets',[[["mmdat"],1],[["mmdat","raw"],3]])],

	['walletgen4',(4,'wallet generation (4) (brainwallet)', [])],
	['addrgen4',  (4,'address generation (4)',              [[["mmdat"],4]])],
	['txcreate4', (4,'tx creation with inputs and outputs from four seed sources, plus non-MMGen inputs and outputs', [[["addrs"],1],[["addrs"],2],[["addrs"],3],[["addrs"],4]])],
	['txsign4',   (4,'tx signing with inputs and outputs from incog file, mnemonic file, wallet and brainwallet, plus non-MMGen inputs and outputs', [[["mmincog"],1],[["mmwords"],2],[["mmdat"],3],[["mmbrain","raw",non_mmgen_fn],4]])],
])

utils = {
	'check_deps': 'check dependencies for specified command, deleting out-of-date files',
	'clean':      'clean specified tmp dir(s) (1,2,3,4; no arg = all tmpdirs)',
}

addrs_per_wallet = 8
cfgs = {
	'1': {
		'tmpdir':        "test/tmp1",
		'wpasswd':       "Dorian",
		'kapasswd':      "Grok the blockchain",
		'addr_idx_list': "12,99,5-10,5,12", # 8 addresses
		'dep_generators':  {
			'mmdat':       "walletgen",
			'addrs':       "addrgen",
			'raw':         "txcreate",
			'sig':         "txsign",
			'mmwords':     "export_mnemonic",
			'mmseed':      "export_seed",
			'mmincog':     "export_incog",
			'mmincox':     "export_incog_hex",
			hincog_fn:    "export_incog_hidden",
			'akeys.mmenc': "keyaddrgen"
		},
	},
	'2': {
		'tmpdir':        "test/tmp2",
		'wpasswd':       "Hodling away",
		'addr_idx_list': "37,45,3-6,22-23",  # 8 addresses
		'dep_generators': {
			'mmdat':       "walletgen2",
			'addrs':       "addrgen2",
			'raw':         "txcreate2",
			'sig':         "txsign2",
			'mmwords':     "export_mnemonic2",
		},
	},
	'3': {
		'tmpdir':        "test/tmp3",
		'wpasswd':       "Major miner",
		'addr_idx_list': "73,54,1022-1023,2-5", # 8 addresses
		'dep_generators': {
			'mmdat':       "walletgen3",
			'addrs':       "addrgen3",
			'raw':         "txcreate3",
			'sig':         "txsign3"
		},
	},
	'4': {
		'tmpdir':        "test/tmp4",
		'wpasswd':       "Hashrate rising",
		'addr_idx_list': "63,1004,542-544,7-9", # 8 addresses
		'dep_generators': {
			'mmdat':       "walletgen4",
			'mmbrain':     "walletgen4",
			'addrs':       "addrgen4",
			'raw':         "txcreate4",
			'sig':         "txsign4",
			non_mmgen_fn:  "txcreate4"
		},
		'bw_filename': "brainwallet.mmbrain",
		'bw_params':   "256,1",
	},
}
cfg = cfgs['1']

from binascii import hexlify
def getrand(n): return int(hexlify(os.urandom(n)),16)
def msgrepr(d): sys.stderr.write(repr(d)+"\n")
def msgrepr_exit(d):
	sys.stderr.write(repr(d)+"\n")
	sys.exit()

# total of two outputs must be < 10 BTC
for k in cfgs.keys():
	cfgs[k]['amts'] = [0,0]
	for idx,mod in (0,6),(1,4):
		cfgs[k]['amts'][idx] = "%s.%s" % ((getrand(2) % mod), str(getrand(4))[:5])

meta_cmds = OrderedDict([
	['gen',    (1,("walletgen","walletchk","addrgen"))],
	['tx',     (1,("txcreate","txsign","txsend"))],
	['export', (1,[k for k in cmd_data if k[:7] == "export_" and cmd_data[k][0] == 1])],
	['gen_sp', (1,[k for k in cmd_data if k[:8] == "addrgen_" and cmd_data[k][0] == 1])],
	['online', (1,("keyaddrgen","txsign_keyaddr"))],
	['2', (2,[k for k in cmd_data if cmd_data[k][0] == 2])],
	['3', (3,[k for k in cmd_data if cmd_data[k][0] == 3])],
	['4', (4,[k for k in cmd_data if cmd_data[k][0] == 4])],
])

from mmgen.Opts import *
help_data = {
	'prog_name': "test.py",
	'desc': "Test suite for the MMGen suite",
	'usage':"[options] [command or metacommand]",
	'options': """
-h, --help         Print this help message
-b, --buf-keypress Use buffered keypresses as with real human input
-d, --debug        Produce debugging output
-e, --exact-output Show the exact output of the MMGen script(s) being run
-l, --list-cmds    List and describe the tests and commands in the test suite
-p, --pause        Pause between tests, resuming on keypress
-q, --quiet        Produce minimal output.  Suppress dependency info
-s, --system       Test scripts and modules installed on system rather than those in the repo root
-v, --verbose      Produce more verbose output
""",
	'notes': """

If no command is given, the whole suite of tests is run.
"""
}

opts,cmd_args = parse_opts(sys.argv,help_data)

if 'system' in opts: sys.path.pop(0)

env = os.environ
if 'buf_keypress' in opts:
	send_delay = 0.3
else:
	send_delay = 0
	env["MMGEN_DISABLE_HOLD_PROTECT"] = "1"

for k in 'debug','verbose','exact_output','pause','quiet':
	globals()[k] = True if k in opts else False

if debug: verbose = True

if exact_output:
	def msg(s): pass
	vmsg = vmsg_r = msg_r = msg
else:
	def msg(s): sys.stderr.write(s+"\n")
	def vmsg(s):
		if verbose: sys.stderr.write(s+"\n")
	def msg_r(s): sys.stderr.write(s)
	def vmsg_r(s):
		if verbose: sys.stderr.write(s)

stderr_save = sys.stderr

def silence():
	if not (verbose or exact_output):
		sys.stderr = open("/dev/null","a")

def end_silence():
	if not (verbose or exact_output):
		sys.stderr = stderr_save

def errmsg(s): stderr_save.write(s+"\n")

def Msg(s): sys.stdout.write(s+"\n")

if "list_cmds" in opts:
	Msg("Available commands:")
	w = max([len(i) for i in cmd_data])
	for cmd in cmd_data:
		Msg("  {:<{w}} - {}".format(cmd,cmd_data[cmd][1],w=w))
	Msg("\nAvailable metacommands:")
	w = max([len(i) for i in meta_cmds])
	for cmd in meta_cmds:
		Msg("  {:<{w}} - {}".format(cmd," + ".join(meta_cmds[cmd][1]),w=w))
	Msg("\nAvailable utilities:")
	w = max([len(i) for i in utils])
	for cmd in sorted(utils):
		Msg("  {:<{w}} - {}".format(cmd,utils[cmd],w=w))
	sys.exit()

import pexpect,time,re
import mmgen.config as g
from mmgen.util import get_data_from_file, write_to_file, get_lines_from_file

redc,grnc,yelc,cyac,reset = (
	["\033[%sm" % c for c in "31;1","32;1","33;1","36;1","0"]
)
def red(s):    return redc+s+reset
def green(s):  return grnc+s+reset
def yellow(s): return yelc+s+reset
def cyan(s):   return cyac+s+reset

def my_send(p,t,delay=send_delay,s=False):
	if delay: time.sleep(delay)
	ret = p.send(t) # returns num bytes written
	if delay: time.sleep(delay)
	if verbose:
		ls = "" if debug or not s else " "
		es = "" if s else "  "
		msg("%sSEND %s%s" % (ls,es,yellow("'%s'"%t.replace('\n',r'\n'))))
	return ret

def my_expect(p,s,t='',delay=send_delay,regex=False,nonl=False):
	quo = "'" if type(s) == str else ""

	if verbose: msg_r("EXPECT %s" % yellow(quo+str(s)+quo))
	else:       msg_r("+")

	try:
		if s == '': ret = 0
		else:
			f = p.expect if regex else p.expect_exact
			ret = f(s,timeout=3)
	except pexpect.TIMEOUT:
		errmsg(red("\nERROR.  Expect %s%s%s timed out.  Exiting" % (quo,s,quo)))
		sys.exit(1)

	if debug or (verbose and type(s) != str): msg_r(" ==> %s " % ret)

	if ret == -1:
		errmsg("Error.  Expect returned %s" % ret)
		sys.exit(1)
	else:
		if t == '':
			if not nonl: vmsg("")
		else: ret = my_send(p,t,delay,s)
		return ret

def cleandir(d):
	try:    files = os.listdir(d)
	except: return

	msg(green("Cleaning directory '%s'" % d))
	for f in files:
		os.unlink(os.path.join(d,f))

def get_file_with_ext(ext,mydir,delete=False):
	flist = [os.path.join(mydir,f)
				for f in os.listdir(mydir) if f.split(".")[-1] == ext]
	if not flist:
		flist = [os.path.join(mydir,f)
			for f in os.listdir(mydir) if ".".join(f.split(".")[-2:]) == ext]
		if not flist:
			return False

	if len(flist) > 1 or delete:
		if not quiet:
			msg("Multiple *.%s files in '%s' - deleting" % (ext,mydir))
		for f in flist: os.unlink(f)
		return False
	else:
		return flist[0]

def get_addrfile_checksum(display=False):
	addrfile = get_file_with_ext("addrs",cfg['tmpdir'])
	silence()
	from mmgen.tx import parse_addrfile
	chk = parse_addrfile(addrfile,{},return_chk_and_sid=True)[0]
	if verbose and display: msg("Checksum: %s" % cyan(chk))
	end_silence()
	return chk

def verify_checksum_or_exit(checksum,chk):
	if checksum != chk:
		errmsg(red("Checksum error: %s" % chk))
		sys.exit(1)
	vmsg(green("Checksums match: %s") % (cyan(chk)))

class MMGenExpect(object):

	def __init__(self,name,mmgen_cmd,cmd_args=[],env=env):
		if not 'system' in opts:
			mmgen_cmd = os.path.join(os.curdir,mmgen_cmd)
		desc = cmd_data[name][1]
		if verbose or exact_output:
			sys.stderr.write(
				green("Testing %s\nExecuting " % desc) +
				cyan("'%s %s'\n" % (mmgen_cmd," ".join(cmd_args)))
			)
		else:
			msg_r("Testing %s " % (desc+":"))
		if env: self.p = pexpect.spawn(mmgen_cmd,cmd_args,env=env)
		else:   self.p = pexpect.spawn(mmgen_cmd,cmd_args)
		if exact_output: self.p.logfile = sys.stdout

	def license(self):
		p = "'w' for conditions and warranty info, or 'c' to continue: "
		my_expect(self.p,p,'c')

	def usr_rand(self,num_chars):
		rand_chars = [chr(ord(i)%94+33) for i in list(os.urandom(num_chars))]
		my_expect(self.p,'symbols left: ','x')
		try:
			vmsg_r("SEND ")
			while self.p.expect('left: ',0.1) == 0:
				ch = rand_chars.pop(0)
				msg_r(yellow(ch)+" " if verbose else "+")
				self.p.send(ch)
		except:
			vmsg("EOT")
		my_expect(self.p,"ENTER to continue: ",'\n')

	def passphrase_new(self,what,passphrase):
		my_expect(self.p,("Enter passphrase for new %s: " % what), passphrase+"\n")
		my_expect(self.p,"Repeat passphrase: ", passphrase+"\n")

	def passphrase(self,what,passphrase):
		my_expect(self.p,("Enter passphrase for %s.*?: " % what),
				passphrase+"\n",regex=True)

	def hash_preset(self,what,preset=''):
		my_expect(self.p,("Enter hash preset for %s, or ENTER .*?:" % what),
				str(preset)+"\n",regex=True)

	def ok(self):
		if verbose or exact_output:
			sys.stderr.write(green("OK\n"))
		else: msg(" OK")

	def written_to_file(self,what,overwrite_unlikely=False,query="Overwrite?  "):
		s1 = "%s written to file " % what
		s2 = query + "Type uppercase 'YES' to confirm: "
		ret = my_expect(self.p,s1 if overwrite_unlikely else [s1,s2])
		if ret == 1:
			my_send(self.p,"YES\n")
			ret = my_expect(self.p,s1)
		outfile = self.p.readline().strip().strip("'")
		vmsg("%s file: %s" % (what,cyan(outfile.replace("'",""))))
		return outfile

	def no_overwrite(self):
		self.expect("Overwrite?  Type uppercase 'YES' to confirm: ","\n")
		self.expect("Exiting at user request")

	def tx_view(self):
		my_expect(self.p,r"View .*?transaction.*? \(y\)es, \(N\)o, \(v\)iew in pager: ","\n",regex=True)

	def expect_getend(self,s,regex=False):
		ret = self.expect(s,regex=regex,nonl=True)
		end = self.readline().strip()
		vmsg(" ==> %s" % cyan(end))
		return end

	def interactive(self):
		return self.p.interact()

	def logfile(self,arg):
		self.p.logfile = arg

	def expect(self,*args,**kwargs):
		return my_expect(self.p,*args,**kwargs)

	def send(self,*args,**kwargs):
		return my_send(self.p,*args,**kwargs)

	def readline(self):
		return self.p.readline()

	def read(self,n):
		return self.p.read(n)


from mmgen.rpc.data import TransactionInfo
from decimal import Decimal
from mmgen.bitcoin import verify_addr

def add_fake_unspent_entry(out,address,comment):
	out.append(TransactionInfo(
		account = unicode(comment),
		vout = (getrand(4) % 8),
		txid = unicode(hexlify(os.urandom(32))),
		amount = Decimal("%s.%s" % (10+(getrand(4) % 40), getrand(4) % 100000000)),
		address = address,
		spendable = False,
		scriptPubKey = ("76a914"+verify_addr(address,return_hex=True)+"88ac"),
		confirmations = getrand(4) % 500
	))

def create_fake_unspent_data(addr_data,unspent_data_file,tx_data,non_mmgen_input=''):

	out = []
	for s in tx_data.keys():
		sid = tx_data[s]['sid']
		for idx in addr_data[sid].keys():
			address = unicode(addr_data[sid][idx][0])
			add_fake_unspent_entry(out,address, "%s:%s Test Wallet" % (sid,idx))

	if non_mmgen_input:
		from mmgen.bitcoin import privnum2addr,hextowif
		privnum = getrand(32)
		btcaddr = privnum2addr(privnum,compressed=True)
		of = os.path.join(cfgs[non_mmgen_input]['tmpdir'],non_mmgen_fn)
		write_to_file(of, hextowif("{:064x}".format(privnum),
					compressed=True)+"\n",{},"compressed bitcoin key")

		add_fake_unspent_entry(out,btcaddr,"Non-MMGen address")

	write_to_file(unspent_data_file,repr(out),{},"Unspent outputs",verbose=True)


def add_comments_to_addr_file(addrfile,tfile):
	silence()
	msg(green("Adding comments to address file '%s'" % addrfile))
	d = get_lines_from_file(addrfile)
	addr_data = {}
	from mmgen.tx import parse_addrfile
	parse_addrfile(addrfile,addr_data)
	sid = addr_data.keys()[0]
	def s(k): return int(k)
	keys = sorted(addr_data[sid].keys(),key=s)
	for n,k in enumerate(keys,1):
		addr_data[sid][k][1] = ("Test address " + str(n))
	d = "#\n# Test address file with comments\n#\n%s {\n%s\n}\n" % (sid,
		"\n".join(["    {:<3} {:<36} {}".format(k,*addr_data[sid][k]) for k in keys]))
	msg_r(d)
	write_to_file(tfile,d,{})
	end_silence()

def make_brainwallet_file(fn):
	# Print random words with random whitespace in between
	from mmgen.mn_tirosh import tirosh_words
	wl = tirosh_words.split("\n")
	nwords,ws_list,max_spaces = 10,"    \n",5
	def rand_ws_seq():
		nchars = getrand(1) % max_spaces + 1
		return "".join([ws_list[getrand(1)%len(ws_list)] for i in range(nchars)])
	rand_pairs = [wl[getrand(4) % len(wl)] + rand_ws_seq() for i in range(nwords)]
	d = "".join(rand_pairs).rstrip() + "\n"
	if verbose: msg_r("Brainwallet password:\n%s" % cyan(d))
	write_to_file(fn,d,{},"brainwallet password")

def do_between():
	if pause:
		from mmgen.util import keypress_confirm
		if keypress_confirm(green("Continue?"),default_yes=True):
			if verbose or exact_output: sys.stderr.write("\n")
		else:
			errmsg("Exiting at user request")
			sys.exit()
	elif verbose or exact_output:
		sys.stderr.write("\n")

def do_cmd(ts,cmd):

	al = []
	for exts,idx in cmd_data[cmd][2]:
		global cfg
		cfg = cfgs[str(idx)]
		for ext in exts:
			while True:
				infile = get_file_with_ext(ext,cfg['tmpdir'])
				if infile:
					al.append(infile); break
				else:
					dg = cfg['dep_generators'][ext]
					if not quiet: msg("Need *.%s from '%s'" % (ext,dg))
					do_cmd(ts,dg)
					do_between()

	MMGenTestSuite.__dict__[cmd](*([ts,cmd] + al))

hincog_bytes   = 1024*1024
hincog_offset  = 98765
hincog_seedlen = 256

rebuild_list = OrderedDict()

def check_if_needs_rebuild(num,ext):
	ret = False

	fn = get_file_with_ext(ext,cfgs[num]['tmpdir'])
	if not fn: ret = True

	cmd = cfgs[num]['dep_generators'][ext]
	deps = [(str(n),e) for exts,n in cmd_data[cmd][2] for e in exts]

	if fn:
		my_age = os.stat(fn).st_mtime
		for num,ext in deps:
			f = get_file_with_ext(ext,cfgs[num]['tmpdir'])
			if f and os.stat(f).st_mtime > my_age: ret = True

	for num,ext in deps:
		if check_if_needs_rebuild(num,ext): ret = True

	if ret and fn:
		if not quiet: msg("File '%s' out of date - deleting" % fn)
		os.unlink(fn)

	rebuild_list[cmd] = ret
	return ret


class MMGenTestSuite(object):

	def __init__(self):
		pass

	def check_deps(self,name,cmds):
		if len(cmds) != 1:
			msg("Usage: %s check_deps <command>" % g.prog_name)
			sys.exit(1)

		cmd = cmds[0]

		if cmd not in cmd_data:
			msg("'%s': unrecognized command" % cmd)
			sys.exit(1)

		d = [(str(num),ext) for exts,num in cmd_data[cmd][2] for ext in exts]

		if not quiet:
			w = "Checking" if d else "No"
			msg("%s dependencies for '%s'" % (w,cmd))

		for num,ext in d:
			check_if_needs_rebuild(num,ext)

		if debug:
			for cmd in rebuild_list:
				msg("cmd: %-15s rebuild: %s" %
						(cmd, cyan("Yes") if rebuild_list[cmd] else "No"))


	def clean(self,name,dirs=[]):
		dirlist = dirs if dirs else cfgs.keys()
		for k in dirlist:
			if k in cfgs:
				cleandir(cfgs[k]['tmpdir'])
			else:
				msg("%s: invalid directory index" % k)
				sys.exit(1)

	def walletgen(self,name,brain=False):
		try: os.mkdir(cfg['tmpdir'],0755)
		except OSError as e:
			if e.errno != 17: raise
		else: msg("Created directory '%s'" % cfg['tmpdir'])
		# cleandir(cfg['tmpdir'])

		args = ["-d",cfg['tmpdir'],"-p1","-r10"]
		if brain:
			bwf = os.path.join(cfg['tmpdir'],cfg['bw_filename'])
			args += ["-b",cfg['bw_params'],bwf]
			make_brainwallet_file(bwf)

		t = MMGenExpect(name,"mmgen-walletgen", args)
		t.license()

		if brain:
			t.expect(
	"A brainwallet will be secure only if you really know what you're doing")
			t.expect("Type uppercase 'YES' to confirm: ","YES\n")

		t.usr_rand(10)
		t.expect("Generating a key from OS random data plus user entropy")

		if not brain:
			t.expect("Generating a key from OS random data plus saved user entropy")

		t.passphrase_new("MMGen wallet",cfg['wpasswd'])
		t.written_to_file("Wallet")
		t.ok()

	def walletchk_beg(self,name,args):
		t = MMGenExpect(name,"mmgen-walletchk", args)
		t.expect("Getting MMGen wallet data from file '%s'" % args[-1])
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		t.expect("Passphrase is OK")
		t.expect("Wallet is OK")
		return t

	def walletchk(self,name,walletfile):
		t = self.walletchk_beg(name,[walletfile])
		t.ok()

	def addrgen(self,name,walletfile):
		t = MMGenExpect(name,"mmgen-addrgen",["-d",cfg['tmpdir'],walletfile,cfg['addr_idx_list']])
		t.license()
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		t.expect("Passphrase is OK")
		t.expect("Generated [0-9]+ addresses",regex=True)
		t.expect_getend(r"Checksum for address data .*?: ",regex=True)
		t.written_to_file("Addresses")
		t.ok()

	def addrimport(self,name,addrfile):
		outfile = os.path.join(cfg['tmpdir'],"addrfile_w_comments")
		add_comments_to_addr_file(addrfile,outfile)
		t = MMGenExpect(name,"mmgen-addrimport",[outfile])
		t.expect_getend(r"checksum for addr data .*\[.*\]: ",regex=True)
		t.expect_getend("Validating addresses...OK. ")
		t.expect("Type uppercase 'YES' to confirm: ","\n")
		vmsg("This is a simulation, so no addresses were actually imported into the tracking\nwallet")
		t.ok()

	def txcreate(self,name,addrfile):
		self.txcreate_common(name,sources=['1'])

	def txcreate_common(self,name,sources=['1'],non_mmgen_input=''):
		if verbose or exact_output:
			sys.stderr.write(green("Generating fake transaction info\n"))
		silence()
		tx_data,addr_data = {},{}
		from mmgen.tx import parse_addrfile
		from mmgen.util import parse_addr_idxs
		for s in sources:
			afile = get_file_with_ext("addrs",cfgs[s]["tmpdir"])
			chk,sid = parse_addrfile(afile,addr_data,return_chk_and_sid=True)
			aix = parse_addr_idxs(cfgs[s]['addr_idx_list'])
			if len(aix) != addrs_per_wallet:
				errmsg(red("Addr index list length != %s: %s" %
							(addrs_per_wallet,repr(aix))))
				sys.exit()
			tx_data[s] = {
				'addrfile': get_file_with_ext("addrs",cfgs[s]['tmpdir']),
				'chk': chk,
				'sid': sid,
				'addr_idxs': aix[-2:],
			}

		unspent_data_file = os.path.join(cfg['tmpdir'],"unspent.json")
		create_fake_unspent_data(addr_data,unspent_data_file,tx_data,non_mmgen_input)

		# make the command line
		from mmgen.bitcoin import privnum2addr
		btcaddr = privnum2addr(getrand(32),compressed=True)

		cmd_args = ["-d",cfg['tmpdir']]
		for num in tx_data.keys():
			s = tx_data[num]
			cmd_args += [
				"%s:%s,%s" % (s['sid'],s['addr_idxs'][0],cfgs[num]['amts'][0]),
			]
			# + one BTC address
			# + one change address and one BTC address
			if num is tx_data.keys()[-1]:
				cmd_args += ["%s:%s" % (s['sid'],s['addr_idxs'][1])]
				cmd_args += ["%s,%s" % (btcaddr,cfgs[num]['amts'][1])]

		for num in tx_data: cmd_args += [tx_data[num]['addrfile']]

		env["MMGEN_BOGUS_WALLET_DATA"] = unspent_data_file
		end_silence()
		if verbose or exact_output: sys.stderr.write("\n")

		t = MMGenExpect(name,"mmgen-txcreate",cmd_args,env)
		t.license()
		for num in tx_data.keys():
			t.expect_getend("Getting address data from file ")
			from mmgen.addr import fmt_addr_idxs
			chk=t.expect_getend(r"Computed checksum for addr data .*?: ",regex=True)
			verify_checksum_or_exit(tx_data[num]['chk'],chk)

		# not in tracking wallet warning, (1 + num sources) times
		if t.expect(["Continue anyway? (y/N): ",
				"Unable to connect to bitcoind"]) == 0:
			t.send("y")
		else:
			errmsg(red("Error: unable to connect to bitcoind.  Exiting"))
			sys.exit(1)

		for num in tx_data.keys():
			t.expect("Continue anyway? (y/N): ","y")
		t.expect(r"'q' = quit sorting, .*?: ","M", regex=True)
		t.expect(r"'q' = quit sorting, .*?: ","q", regex=True)
		outputs_list = [addrs_per_wallet*i + 1 for i in range(len(tx_data))]
		if non_mmgen_input: outputs_list.append(len(tx_data)*addrs_per_wallet + 1)
		t.expect("Enter a range or space-separated list of outputs to spend: ",
				" ".join([str(i) for i in outputs_list])+"\n")
		if non_mmgen_input: t.expect("Accept? (y/N): ","y")
		t.expect("OK? (Y/n): ","y")
		t.expect("Add a comment to transaction? (y/N): ","\n")
		t.tx_view()
		t.expect("Save transaction? (Y/n): ","\n")
		t.written_to_file("Transaction")
		t.ok()

	def txsign(self,name,txfile,walletfile):
		t = MMGenExpect(name,"mmgen-txsign", ["-d",cfg['tmpdir'],txfile,walletfile])
		t.license()
		t.tx_view()
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.written_to_file("Signed transaction")
		t.ok()

	def txsend(self,name,sigfile):
		t = MMGenExpect(name,"mmgen-txsend", ["-d",cfg['tmpdir'],sigfile])
		t.license()
		t.tx_view()
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.expect("Are you sure you want to broadcast this transaction to the network?")
		t.expect("Type uppercase 'YES, I REALLY WANT TO DO THIS' to confirm: ","\n")
		t.expect("Exiting at user request")
		vmsg("This is a simulation, so no transaction was sent")
		t.ok()

	def export_seed(self,name,walletfile):
		t = self.walletchk_beg(name,["-s","-d",cfg['tmpdir'],walletfile])
		f = t.written_to_file("Seed data")
		silence()
		msg("Seed data: %s" % cyan(get_data_from_file(f,"seed data")))
		end_silence()
		t.ok()

	def export_mnemonic(self,name,walletfile):
		t = self.walletchk_beg(name,["-m","-d",cfg['tmpdir'],walletfile])
		f = t.written_to_file("Mnemonic data")
		silence()
		msg_r("Mnemonic data: %s" % cyan(get_data_from_file(f,"mnemonic data")))
		end_silence()
		t.ok()

	def export_incog(self,name,walletfile,args=["-g"]):
		t = MMGenExpect(name,"mmgen-walletchk",args+["-d",cfg['tmpdir'],"-r","10",walletfile])
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		t.usr_rand(10)
		t.expect_getend("Incog ID: ")
		if args[0] == "-G": return t
		t.written_to_file("Incognito wallet data",overwrite_unlikely=True)
		t.ok()

	def export_incog_hex(self,name,walletfile):
		self.export_incog(name,walletfile,args=["-X"])

	# TODO: make outdir and hidden incog compatible (ignore --outdir and warn user?)
	def export_incog_hidden(self,name,walletfile):
		rf,rd = os.path.join(cfg['tmpdir'],hincog_fn),os.urandom(hincog_bytes)
		vmsg(green("Writing %s bytes of data to file '%s'" % (hincog_bytes,rf)))
		write_to_file(rf,rd,{},verbose=verbose)
		t = self.export_incog(name,walletfile,args=["-G","%s,%s"%(rf,hincog_offset)])
		t.written_to_file("Data",query="")
		t.ok()

	def addrgen_seed(self,name,walletfile,foo,what="seed data",arg="-s"):
		t = MMGenExpect(name,"mmgen-addrgen",
				[arg,"-d",cfg['tmpdir'],walletfile,cfg['addr_idx_list']])
		t.license()
		t.expect_getend("Valid %s for seed ID " % what)
		vmsg("Comparing generated checksum with checksum from previous address file")
		chk = t.expect_getend(r"Checksum for address data .*?: ",regex=True)
		verify_checksum_or_exit(get_addrfile_checksum(),chk)
		t.no_overwrite()
		t.ok()

	def addrgen_mnemonic(self,name,walletfile,foo):
		self.addrgen_seed(name,walletfile,foo,what="mnemonic",arg="-m")

	def addrgen_incog(self,name,walletfile,foo,args=["-g"]):
		t = MMGenExpect(name,"mmgen-addrgen",args+["-d",
				cfg['tmpdir'],walletfile,cfg['addr_idx_list']])
		t.license()
		t.expect_getend("Incog ID: ")
		t.passphrase("MMGen incognito wallet \w{8}", cfg['wpasswd'])
		t.hash_preset("incog wallet",'1')
		vmsg("Comparing generated checksum with checksum from address file")
		chk = t.expect_getend(r"Checksum for address data .*?: ",regex=True)
		verify_checksum_or_exit(get_addrfile_checksum(),chk)
		t.no_overwrite()
		t.ok()

	def addrgen_incog_hex(self,name,walletfile,foo):
		self.addrgen_incog(name,walletfile,foo,args=["-X"])

	def addrgen_incog_hidden(self,name,walletfile,foo):
		rf = os.path.join(cfg['tmpdir'],hincog_fn)
		self.addrgen_incog(name,walletfile,foo,
				args=["-G","%s,%s,%s"%(rf,hincog_offset,hincog_seedlen)])

	def keyaddrgen(self,name,walletfile):
		t = MMGenExpect(name,"mmgen-keygen",
				["-d",cfg['tmpdir'],walletfile,cfg['addr_idx_list']])
		t.license()
		t.expect("Type uppercase 'YES' to confirm: ","YES\n")
		t.passphrase("MMGen wallet",cfg['wpasswd'])
		t.expect_getend(r"Checksum for key-address data .*?: ",regex=True)
		t.expect("Encrypt key list? (y/N): ","y")
		t.hash_preset("new key list",'1')
		t.passphrase_new("key list",cfg['kapasswd'])
		t.written_to_file("Keys")
		t.ok()

	def txsign_keyaddr(self,name,keyaddr_file,txfile):
		t = MMGenExpect(name,"mmgen-txsign", ["-d",cfg['tmpdir'],"-M",keyaddr_file,txfile])
		t.license()
		t.hash_preset("key-address file",'1')
		t.passphrase("key-address file",cfg['kapasswd'])
		t.expect("Check key-to-address validity? (y/N): ","y")
		t.expect("View data for transaction? (y)es, (N)o, (v)iew in pager: ","\n")
		t.expect("Signing transaction...OK")
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.written_to_file("Signed transaction")
		t.ok()

	def walletgen2(self,name):
		global cfg
		cfg = cfgs['2']
		self.walletgen(name)

	def addrgen2(self,name,walletfile):
		self.addrgen(name,walletfile)

	def txcreate2(self,name,addrfile):
		self.txcreate_common(name,sources=['2'])

	def txsign2(self,name,txf1,wf1,txf2,wf2):
		t = MMGenExpect(name,"mmgen-txsign", ["-d",cfg['tmpdir'],txf1,wf1,txf2,wf2])
		t.license()

		for cnum in ['1','2']:
			t.tx_view()
			t.passphrase("MMGen wallet",cfgs[cnum]['wpasswd'])
			t.expect_getend("Signing transaction ")
			t.expect("Edit transaction comment? (y/N): ","\n")
			t.written_to_file("Signed transaction #%s" % cnum)

		t.ok()

	def export_mnemonic2(self,name,walletfile):
		self.export_mnemonic(name,walletfile)

	def walletgen3(self,name):
		global cfg
		cfg = cfgs['3']
		self.walletgen(name)

	def addrgen3(self,name,walletfile):
		self.addrgen(name,walletfile)

	def txcreate3(self,name,addrfile1,addrfile2):
		self.txcreate_common(name,sources=['1','3'])

	def txsign3(self,name,wf1,wf2,txf2):
		t = MMGenExpect(name,"mmgen-txsign", ["-d",cfg['tmpdir'],wf1,wf2,txf2])
		t.license()
		t.tx_view()

		for s in ['1','3']:
			t.expect_getend("Getting MMGen wallet data from file ")
			t.passphrase("MMGen wallet",cfgs[s]['wpasswd'])

		t.expect_getend("Signing transaction")
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.written_to_file("Signed transaction")
		t.ok()

	def walletgen4(self,name):
		global cfg
		cfg = cfgs['4']
		self.walletgen(name,brain=True)

	def addrgen4(self,name,walletfile):
		self.addrgen(name,walletfile)

	def txcreate4(self,name,f1,f2,f3,f4):
		self.txcreate_common(name,sources=['1','2','3','4'],non_mmgen_input='4')

	def txsign4(self,name,f1,f2,f3,f4,f5,non_mm_fn):
		t = MMGenExpect(name,"mmgen-txsign",
			["-d",cfg['tmpdir'],"-b",cfg['bw_params'],"-k",non_mm_fn,f1,f2,f3,f4,f5])
		t.license()
		t.tx_view()

		for cfgnum,what,app in ('1',"incognito"," incognito"),('3',"MMGen",""):
			t.expect_getend("Getting %s wallet data from file " % what)
			t.passphrase("MMGen%s wallet"%app,cfgs[cfgnum]['wpasswd'])
			if cfgnum == '1':
				t.hash_preset("incog wallet",'1')

		t.expect_getend("Signing transaction")
		t.expect("Edit transaction comment? (y/N): ","\n")
		t.written_to_file("Signed transaction")
		t.ok()

# main()
ts = MMGenTestSuite()
start_time = int(time.time())

if pause:
	import termios,atexit
	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)
	def at_exit():
		termios.tcsetattr(fd, termios.TCSADRAIN, old)
	atexit.register(at_exit)

try:
	if cmd_args:
		arg1 = cmd_args[0]
		if arg1 in utils:
			if arg1 == "check_deps": debug = True
			MMGenTestSuite.__dict__[arg1](ts,arg1,cmd_args[1:])
			sys.exit()
		elif arg1 in meta_cmds:
			if len(cmd_args) == 1:
				ts.clean("clean",str(meta_cmds[arg1][0]))
				for cmd in meta_cmds[arg1][1]:
					do_cmd(ts,cmd)
					if cmd is not cmd_data.keys()[-1]: do_between()
			else:
				msg("Only one meta command may be specified")
				sys.exit(1)
		elif arg1 in cmd_data:
			if len(cmd_args) == 1:
				ts.check_deps("check_deps",[arg1])
				do_cmd(ts,arg1)
			else:
				msg("Only one command may be specified")
				sys.exit(1)
		else:
			errmsg("%s: unrecognized command" % arg1)
			sys.exit(1)
	else:
		ts.clean("clean")
		for cmd in cmd_data:
			do_cmd(ts,cmd)
			if cmd is not cmd_data.keys()[-1]: do_between()
except:
	sys.stderr = stderr_save
	raise

t = int(time.time()) - start_time
msg(green(
	"All requested tests finished OK, elapsed time: %02i:%02i" % (t/60,t%60)))
