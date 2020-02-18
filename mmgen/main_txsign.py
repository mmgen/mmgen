#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
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

from mmgen.common import *
from mmgen.obj import SubSeedIdxRange
from mmgen.seed import SeedSource

# -w, --use-wallet-dat (keys from running coin daemon) removed: use walletdump rpc instead
opts_data = {
	'sets': [('yes', True, 'quiet', True)],
	'text': {
		'desc':    'Sign cryptocoin transactions generated by {pnl}-txcreate'.format(pnl=g.proj_name.lower()),
		'usage':   '[opts] <transaction file>... [seed source]...',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-b, --brain-params=l,p Use seed length 'l' and hash preset 'p' for
                      brainwallet input
-d, --outdir=      d  Specify an alternate directory 'd' for output
-D, --tx-id           Display transaction ID and exit
-e, --echo-passphrase Print passphrase to screen when typing it
-E, --use-internal-keccak-module Force use of the internal keccak module
-i, --in-fmt=      f  Input is from wallet format 'f' (see FMT CODES below)
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-O, --old-incog-fmt   Specify old-format incognito input
-l, --seed-len=    l  Specify wallet seed length of 'l' bits. This option
                      is required only for brainwallet and incognito inputs
                      with non-standard (< {g.seed_len}-bit) seed lengths.
-p, --hash-preset=p   Use the scrypt hash parameters defined by preset 'p'
                      for password hashing (default: '{g.hash_preset}')
-z, --show-hash-presets Show information on available hash presets
-k, --keys-from-file=f Provide additional keys for non-{pnm} addresses
-K, --key-generator=m Use method 'm' for public key generation
                      Options: {kgs} (default: {kg})
-M, --mmgen-keys-from-file=f Provide keys for {pnm} addresses in a key-
                      address file (output of '{pnl}-keygen'). Permits
                      online signing without an {pnm} seed source. The
                      key-address file is also used to verify {pnm}-to-{cu}
                      mappings, so the user should record its checksum.
-P, --passwd-file= f  Get {pnm} wallet or {dn} passphrase from file 'f'
-q, --quiet           Suppress warnings; overwrite files without prompting
-I, --info            Display information about the transaction and exit
-t, --terse-info      Like '--info', but produce more concise output
-u, --subseeds=     n The number of subseed pairs to scan for (default: {ss},
                      maximum: {ss_max}). Only the default or first supplied
                      wallet is scanned for subseeds.
-v, --verbose         Produce more verbose output
-V, --vsize-adj=   f  Adjust transaction's estimated vsize by factor 'f'
-y, --yes             Answer 'yes' to prompts, suppress non-essential output
""",
	'notes': """
{}
Seed source files must have the canonical extensions listed in the 'FileExt'
column below:

  {f}
"""
	},
	'code': {
		'options': lambda s: s.format(
			g=g,pnm=g.proj_name,pnl=g.proj_name.lower(),dn=g.proto.daemon_name,
			kgs=' '.join(['{}:{}'.format(n,k) for n,k in enumerate(g.key_generators,1)]),
			kg=g.key_generator,
			ss=g.subseeds,ss_max=SubSeedIdxRange.max_idx,
			cu=g.coin),
		'notes': lambda s: s.format(
			help_notes('txsign'),
			f='\n  '.join(SeedSource.format_fmt_codes().splitlines()))
	}
}

infiles = opts.init(opts_data,add_opts=['b16'])

if not infiles: opts.usage()
for i in infiles: check_infile(i)

if g.proto.sign_mode == 'daemon':
	rpc_init()

if not opt.info and not opt.terse_info:
	do_license_msg(immed=True)

from mmgen.txsign import *

tx_files   = get_tx_files(opt,infiles)
seed_files = get_seed_files(opt,infiles)

kal        = get_keyaddrlist(opt)
kl         = get_keylist(opt)
if kl and kal: kl.remove_dup_keys(kal)

tx_num_str,bad_tx_count = '',0
for tx_num,tx_file in enumerate(tx_files,1):
	if len(tx_files) > 1:
		msg('\nTransaction #{} of {}:'.format(tx_num,len(tx_files)))
		tx_num_str = ' #{}'.format(tx_num)
	tx = MMGenTX(tx_file,offline=True)

	if tx.marked_signed():
		msg('Transaction is already signed!'); continue

	vmsg("Successfully opened transaction file '{}'".format(tx_file))

	if opt.tx_id:
		msg(tx.txid); continue

	if opt.info or opt.terse_info:
		tx.view(pause=False,terse=opt.terse_info); continue

	if not opt.yes:
		tx.view_with_prompt('View data for transaction{}?'.format(tx_num_str))

	if txsign(tx,seed_files,kl,kal,tx_num_str):
		if not opt.yes:
			tx.add_comment() # edits an existing comment
		tx.write_to_file(ask_write=not opt.yes,ask_write_default_yes=True,add_desc=tx_num_str)
	else:
		ymsg('Transaction could not be signed')
		bad_tx_count += 1

if bad_tx_count:
	ydie(2,'{} transaction{} could not be signed'.format(bad_tx_count,suf(bad_tx_count)))
