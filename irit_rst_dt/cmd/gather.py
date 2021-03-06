# Author: Eric Kow
# License: CeCILL-B (French BSD3-like)

"""
gather features
"""

from __future__ import print_function
from os import path as fp
import os

from attelo.harness.util import call, force_symlink

from ..local import (TEST_CORPUS,
                     TRAINING_CORPUS,
                     PTB_DIR,
                     FEATURE_SET,
                     CORENLP_OUT_DIR,
                     LECSIE_DATA_DIR)
from ..util import (current_tmp, latest_tmp)

NAME = 'gather'


def config_argparser(psr):
    """Subcommand flags.

    You should create and pass in the subparser to which the flags
    are to be added.

    Notes
    -----
    Could we remove intermediary layers and indirections?
    For example, this script is a wrapper around
    `educe.rst_dt.learning.cmd.extract`.
    This means we need to explicitly expose some (or all?) of the
    arguments of the latter script in the current one.
    This does not look like a good idea.
    """
    psr.add_argument('--skip-training',
                     action='store_true',
                     help='only gather test data')
    psr.add_argument('--coarse',
                     action='store_true',
                     help='use coarse-grained labels')
    psr.add_argument('--fix_pseudo_rels',
                        action='store_true',
                        help='fix pseudo-relation labels')
    psr.set_defaults(func=main)


def extract_features(corpus, output_dir, coarse, fix_pseudo_rels,
                     vocab_path=None,
                     label_path=None):
    """Extract instances from a corpus, store them in files.

    Run feature extraction for a particular corpus and store the
    results in the output directory. Output file name will be
    computed from the corpus file name.

    Parameters
    ----------
    corpus: filepath
        Path to the corpus.
    output_dir: filepath
        Path to the output folder.
    coarse: boolean, False by default
        Use coarse-grained relation labels.
    fix_pseudo_rels: boolean, False by default
        Rewrite pseudo-relations to improve consistency (WIP).
    vocab_path: filepath
        Path to a fixed vocabulary mapping, for feature extraction
        (needed if extracting test data: the same vocabulary should be
        used in train and test).
    label_path: filepath
        Path to a list of labels.
    """
    # TODO: perhaps we could just directly invoke the appropriate
    # educe module here instead of going through the command line?
    cmd = [
        "rst-dt-learning", "extract",
        corpus,
        PTB_DIR,  # TODO make this optional and exclusive from CoreNLP
        output_dir,
        '--feature_set', FEATURE_SET,
    ]
    # NEW 2016-05-19 rewrite pseudo-relations
    if fix_pseudo_rels:
        cmd.extend([
            '--fix_pseudo_rels'
        ])
    # NEW 2016-05-03 use coarse- or fine-grained relation labels
    # NB "coarse" was the previous default
    if coarse:
        cmd.extend([
            '--coarse'
        ])
    if CORENLP_OUT_DIR is not None:
        cmd.extend([
            '--corenlp_out_dir', CORENLP_OUT_DIR,
        ])
    if LECSIE_DATA_DIR is not None:
        cmd.extend([
            '--lecsie_data_dir', LECSIE_DATA_DIR,
        ])
    if vocab_path is not None:
        cmd.extend(['--vocabulary', vocab_path])
    if label_path is not None:
        cmd.extend(['--labels', label_path])
    call(cmd)


def main(args):
    """
    Subcommand main.

    You shouldn't need to call this yourself if you're using
    `config_argparser`
    """
    if args.skip_training:
        tdir = latest_tmp()
    else:
        tdir = current_tmp()
        extract_features(TRAINING_CORPUS, tdir, args.coarse,
                         args.fix_pseudo_rels)
    if TEST_CORPUS is not None:
        train_path = fp.join(tdir, fp.basename(TRAINING_CORPUS))
        label_path = train_path + '.relations.sparse'
        vocab_path = label_path + '.vocab'
        extract_features(TEST_CORPUS, tdir, args.coarse,
                         args.fix_pseudo_rels,
                         vocab_path=vocab_path,
                         label_path=label_path)
    with open(os.path.join(tdir, "versions-gather.txt"), "w") as stream:
        call(["pip", "freeze"], stdout=stream)
    if not args.skip_training:
        latest_dir = latest_tmp()
        force_symlink(fp.basename(tdir), latest_dir)
