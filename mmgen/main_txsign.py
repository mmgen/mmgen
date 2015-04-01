#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2015 Philemon <mmgen-py@yandex.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
mmgen-txsign: Sign a transaction generated by 'mmgen-txcreate'
"""

import sys

import mmgen.config as g
import mmgen.opt as opt
from mmgen.tx import *
from mmgen.util import do_license_msg

opts_data = {
	'desc':    "Sign Bitcoin transactions generated by {}-txcreate".format(g.proj_name.lower()),
	'usage':   "[opts] <transaction file> .. [mmgen wallet/seed/words/brainwallet file] ..",
	'options': """
-h, --help               Print this help message
-d, --outdir=         d  Specify an alternate directory 'd' for output
-e, --echo-passphrase    Print passphrase to screen when typing it
-i, --info               Display information about the transaction and exit
-t, --terse-info         Like '--info', but produce more concise output
-I, --tx-id              Display transaction ID and exit
-k, --keys-from-file= f  Provide additional keys for non-{MMG} addresses
-K, --no-keyconv         Force use of internal libraries for address gener-
                         ation, even if 'keyconv' is available
-M, --mmgen-keys-from-file=f  Provide keys for {MMG} addresses in a key-
                         address file (output of '{mmg}-keygen'). Permits
                         online signing without an {MMG} seed source.
                         The key-address file is also used to verify
                         {MMG}-to-BTC mappings, so its checksum should
                         be recorded by the user.
-P, --passwd-file=    f  Get MMGen wallet or bitcoind passphrase from file 'f'
-q, --quiet              Suppress warnings; overwrite files without
                         prompting
-v, --verbose            Produce more verbose output
-b, --from-brain=    l,p Generate keys from a user-created password,
                         i.e. a "brainwallet", using seed length 'l' and
                         hash preset 'p'
-w, --use-wallet-dat     Get keys from a running bitcoind
-g, --from-incog         Generate keys from an incognito wallet
-X, --from-incog-hex     Generate keys from an incognito hexadecimal wallet
-G, --from-incog-hidden= f,o,l  Generate keys from incognito data in file
                         'f' at offset 'o', with seed length of 'l'
-o, --old-incog-fmt      Use old (pre-0.7.8) incog format
-m, --from-mnemonic      Generate keys from an electrum-like mnemonic
-s, --from-seed          Generate keys from a seed in .{g.seed_ext} format
""".format(g=g,MMG=g.proj_name,mmg=g.proj_name.lower()),
	'notes': """

Transactions with either {MMG} or non-{MMG} input addresses may be signed.
For non-{MMG} inputs, the bitcoind wallet.dat is used as the key source.
For {MMG} inputs, key data is generated from your seed as with the
{mmg}-addrgen and {mmg}-keygen utilities.

Data for the --from-<what> options will be taken from a file if a second
file is specified on the command line.  Otherwise, the user will be
prompted to enter the data.

In cases of transactions with mixed {MMG} and non-{MMG} inputs, non-{MMG}
keys must be supplied in a separate file (WIF format, one key per line)
using the '--keys-from-file' option.  Alternatively, one may get keys from
a running bitcoind using the '--force-wallet-dat' option.  First import the
required {MMG} keys using 'bitcoind importprivkey'.

For transaction outputs that are {MMG} addresses, {MMG}-to-Bitcoin address
mappings are verified.  Therefore, seed material or a key-address file for
these addresses must be supplied on the command line.

Seed data supplied in files must have the following extensions:
   wallet:      '.{g.wallet_ext}'
   seed:        '.{g.seed_ext}'
   mnemonic:    '.{g.mn_ext}'
   brainwallet: '.{g.brain_ext}'
""".format(g=g,MMG=g.proj_name,mmg=g.proj_name.lower())
}

wmsg = {
	'mm2btc_mapping_error': """
MMGen -> BTC address mappings differ!
From %-18s %s -> %s
From %-18s %s -> %s
""".strip(),
	'removed_dups': """
Removed %s duplicate wif key%s from keylist (also in {MMG} key-address file
""".strip().format(MMG=g.proj_name),
}

def get_seed_for_seed_id(seed_id,infiles,saved_seeds):

	if seed_id in saved_seeds.keys():
		return saved_seeds[seed_id]

	from mmgen.crypto import get_seed_retry

	while True:
		if infiles:
			seed = get_seed_retry(infiles.pop(0))
		elif any([opt.from_brain,opt.from_mnemonic,opt.from_seed,opt.from_incog]):
			qmsg("Need seed data for seed ID %s" % seed_id)
			seed = get_seed_retry("",seed_id)
			msg("User input produced seed ID %s" % make_chksum_8(seed))
		else:
			msg("ERROR: No seed source found for seed ID: %s" % seed_id)
			sys.exit(2)

		sid = make_chksum_8(seed)
		saved_seeds[sid] = seed

		if sid == seed_id: return seed


def get_keys_for_mmgen_addrs(mmgen_addrs,infiles,saved_seeds):

	seed_ids = set([i[:8] for i in mmgen_addrs])
	vmsg("Need seed%s: %s" % (suf(seed_ids,"k")," ".join(seed_ids)))
	d = []

	from mmgen.addr import generate_addrs
	for seed_id in seed_ids:
		# Returns only if seed is found
		seed = get_seed_for_seed_id(seed_id,infiles,saved_seeds)
		addr_nums = [int(i[9:]) for i in mmgen_addrs if i[:8] == seed_id]
		opt.gen_what = "ka"
		ai = generate_addrs(seed,addr_nums)
		d += [("{}:{}".format(seed_id,e.idx),e.addr,e.wif) for e in ai.addrdata]
	return d


def sign_transaction(c,tx_hex,tx_num_str,sig_data,keys=None):

	if keys:
		qmsg("Passing %s key%s to bitcoind" % (len(keys),suf(keys,"k")))
		if opt.debug: Msg("Keys:\n  %s" % "\n  ".join(keys))

	msg_r("Signing transaction{}...".format(tx_num_str))
	from mmgen.rpc import exceptions
	try:
		sig_tx = c.signrawtransaction(tx_hex,sig_data,keys)
	except exceptions.InvalidAddressOrKey:
		msg("failed\nInvalid address or key")
		sys.exit(3)

	return sig_tx


def sign_tx_with_bitcoind_wallet(c,tx_hex,tx_num_str,sig_data,keys):

	try:
		sig_tx = sign_transaction(c,tx_hex,tx_num_str,sig_data,keys)
	except:
		from mmgen.rpc import exceptions
		msg("Using keys in wallet.dat as per user request")
		prompt = "Enter passphrase for bitcoind wallet: "
		while True:
			passwd = get_bitcoind_passphrase(prompt)

			try:
				c.walletpassphrase(passwd, 9999)
			except exceptions.WalletPassphraseIncorrect:
				msg("Passphrase incorrect")
			else:
				msg("Passphrase OK"); break

		sig_tx = sign_transaction(c,tx_hex,tx_num_str,sig_data,keys)

		msg("Locking wallet")
		try:
			c.walletlock()
		except:
			msg("Failed to lock wallet")

	return sig_tx


def check_maps_from_seeds(maplist,label,infiles,saved_seeds,return_keys=False):

	if not maplist: return []
	qmsg("Checking MMGen -> BTC address mappings for %ss (from seeds)" % label)
	d = get_keys_for_mmgen_addrs(maplist.keys(),infiles,saved_seeds)
#	0=mmaddr 1=addr 2=wif
	m = dict([(e[0],e[1]) for e in d])
	for a,b in zip(sorted(m),sorted(maplist)):
		if a != b:
			al,bl = "generated seed:","tx file:"
			msg(wmsg['mm2btc_mapping_error'] % (al,a,m[a],bl,b,maplist[b]))
			sys.exit(3)
	if return_keys:
		ret = [e[2] for e in d]
		vmsg("Added %s wif key%s from seeds" % (len(ret),suf(ret,"k")))
		return ret

def missing_keys_errormsg(addrs):
	Msg("""
A key file must be supplied (or use the '--use-wallet-dat' option)
for the following non-{} address{}:\n    {}""".format(
	g.proj_name,suf(addrs,"a"),"\n    ".join(addrs)).strip())


def parse_mmgen_keyaddr_file():
	from mmgen.addr import AddrInfo
	ai = AddrInfo(opt.mmgen_keys_from_file,has_keys=True)
	vmsg("Found %s wif key%s for seed ID %s" %
			(ai.num_addrs, suf(ai.num_addrs,"k"), ai.seed_id))
	# idx: (0=addr, 1=comment 2=wif) -> mmaddr: (0=addr, 1=wif)
	return dict(
		[("%s:%s"%(ai.seed_id,e.idx), (e.addr,e.wif)) for e in ai.addrdata])


def parse_keylist(from_file):
	fn = opt.keys_from_file
	d = get_data_from_file(fn,"non-%s keylist" % g.proj_name)
	enc_ext = get_extension(fn) == g.mmenc_ext
	if enc_ext or not is_utf8(d):
		if not enc_ext: qmsg("Keylist file appears to be encrypted")
		from crypto import mmgen_decrypt_retry
		d = mmgen_decrypt_retry(d,"encrypted keylist")
	# Check for duplication with key-address file
	keys_all = set(remove_comments(d.split("\n")))
	d = from_file['mmdata']
	kawifs = [d[k][1] for k in d.keys()]
	keys = [k for k in keys_all if k not in kawifs]
	removed = len(keys_all) - len(keys)
	if removed: vmsg(wmsg['removed_dups'] % (removed,suf(removed,"k")))
	addrs = []
	wif2addr_f = get_wif2addr_f()
	for n,k in enumerate(keys,1):
		qmsg_r("\rGenerating addresses from keylist: %s/%s" % (n,len(keys)))
		addrs.append(wif2addr_f(k))
	qmsg("\rGenerated addresses from keylist: %s/%s " % (n,len(keys)))

	return dict(zip(addrs,keys))


# Check inputs and outputs maps against key-address file, deleting entries:
def check_maps_from_kafile(imap,what,kadata,return_keys=False):
	qmsg("Checking MMGen -> BTC address mappings for %ss (from key-address file)" % what)
	ret = []
	for k in imap.keys():
		if k in kadata.keys():
			if kadata[k][0] == imap[k]:
				del imap[k]
				ret += [kadata[k][1]]
			else:
				kl,il = "key-address file:","tx file:"
				msg(wmsg['mm2btc_mapping_error']%(kl,k,kadata[k][0],il,k,imap[k]))
				sys.exit(2)
	if ret: vmsg("Removed %s address%s from %ss map" % (len(ret),suf(ret,"a"),what))
	if return_keys:
		vmsg("Added %s wif key%s from %ss map" % (len(ret),suf(ret,"k"),what))
		return ret


def get_keys_from_keylist(kldata,other_addrs):
	ret = []
	for addr in other_addrs[:]:
		if addr in kldata.keys():
			ret += [kldata[addr]]
			other_addrs.remove(addr)
	vmsg("Added %s wif key%s from user-supplied keylist" %
			(len(ret),suf(ret,"k")))
	return ret


infiles = opt.opts.init(opts_data,add_opts=["b16"])

for l in (
('tx_id', 'info'),
('tx_id', 'terse_info'),
): opt.opts.warn_incompatible_opts(l)

if opt.from_incog_hex or opt.from_incog_hidden: opt.from_incog = True

if not infiles: opt.opts.usage()
for i in infiles: check_infile(i)

c = connect_to_bitcoind()

saved_seeds = {}
tx_files   = [i for i in infiles if get_extension(i) == g.rawtx_ext]
seed_files = [i for i in infiles if get_extension(i) != g.rawtx_ext]

if not opt.info and not opt.terse_info:
	do_license_msg(immed=True)

from_file = { 'mmdata':{}, 'kldata':{} }
if opt.mmgen_keys_from_file:
	from_file['mmdata'] = parse_mmgen_keyaddr_file() or {}
if opt.keys_from_file:
	from_file['kldata'] = parse_keylist(from_file) or {}

tx_num_str = ""
for tx_num,tx_file in enumerate(tx_files,1):
	if len(tx_files) > 1:
		msg("\nTransaction #%s of %s:" % (tx_num,len(tx_files)))
		tx_num_str = " #%s" % tx_num

	m = "" if opt.tx_id else "transaction data"
	tx_data = get_lines_from_file(tx_file,m)

	metadata,tx_hex,inputs_data,b2m_map,comment = parse_tx_file(tx_data,tx_file)
	vmsg("Successfully opened transaction file '%s'" % tx_file)

	if opt.tx_id:
		msg(metadata[0])
		sys.exit(0)

	if opt.info or opt.terse_info:
		view_tx_data(c,inputs_data,tx_hex,b2m_map,comment,metadata,pause=False,
				terse=opt.terse_info)
		sys.exit(0)

	prompt_and_view_tx_data(c,"View data for transaction{}?".format(tx_num_str),
		inputs_data,tx_hex,b2m_map,comment,metadata)

	# Start
	other_addrs = list(set([i['address'] for i in inputs_data if not i['mmid']]))

	keys = get_keys_from_keylist(from_file['kldata'],other_addrs)

	if other_addrs and not opt.use_wallet_dat:
		missing_keys_errormsg(other_addrs)
		sys.exit(2)

	imap = dict([(i['mmid'],i['address']) for i in inputs_data if i['mmid']])
	omap = dict([(j[0],i) for i,j in b2m_map.items()])
	sids = set([i[:8] for i in imap.keys()])

	keys += check_maps_from_kafile(imap,"input",from_file['mmdata'],True)
	check_maps_from_kafile(omap,"output",from_file['mmdata'])

	keys += check_maps_from_seeds(imap,"input",seed_files,saved_seeds,True)
	check_maps_from_seeds(omap,"output",seed_files,saved_seeds)

	extra_sids = set(saved_seeds.keys()) - sids
	if extra_sids:
		msg("Unused seed ID%s: %s" %
			(suf(extra_sids,"k")," ".join(extra_sids)))

	# Begin signing
	sig_data = [
		{"txid":i['txid'],"vout":i['vout'],"scriptPubKey":i['scriptPubKey']}
			for i in inputs_data]

	if opt.use_wallet_dat:
		sig_tx = sign_tx_with_bitcoind_wallet(
				c,tx_hex,tx_num_str,sig_data,keys)
	else:
		sig_tx = sign_transaction(c,tx_hex,tx_num_str,sig_data,keys)

	if sig_tx['complete']:
		msg("OK")
		if keypress_confirm("Edit transaction comment?"):
			comment = get_tx_comment_from_user(comment)
		outfile = "tx_%s[%s].%s" % (metadata[0],metadata[1],g.sigtx_ext)
		data = make_tx_data("{} {} {t}".format(*metadata[:2], t=make_timestamp()),
				sig_tx['hex'], inputs_data, b2m_map, comment)
		w = "signed transaction{}".format(tx_num_str)
		write_to_file(outfile,data,w,(not opt.quiet),True,False)
	else:
		msg_r("failed\nSome keys were missing.  ")
		msg("Transaction %scould not be signed." % tx_num_str)
		sys.exit(3)
