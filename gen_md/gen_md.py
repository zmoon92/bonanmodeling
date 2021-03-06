# 
"""
Generate md files from the Matlab scripts. 

"""

# from glob import glob
import os
from pathlib import Path
import shutil

import yaml


ROOT = Path('../')  # project root. assumes we are running this from this scripts location!

MD_OUT_ROOT = ROOT / "docs/pages"

# to use when creating the links to the source files on GH
# can also use Jekyll github-metadata plugin
REPO_ROOT_URL_FOR_LINKS = "https://github.com/zmoon92/bonanmodeling/tree/master"
# REPO_ROOT_URL_FOR_RAW_LINKS = "https://raw.githubusercontent.com/zmoon92/bonanmodeling/gh-pages-dev"
REPO_ROOT_URL_FOR_RAW_LINKS = "https://raw.githubusercontent.com/zmoon92/bonanmodeling/master"

def md_matlab_program(p, main=True):
    """Create markdown to add to page for a given Matlab program.
    
    p : Path
        to the Matlab program

    main : bool
        whether to tag as a main program 
        (with the kramdown IAL)

    Returns
    -------
    str
        of the md snippet to be included in the page
    
    """

    program_name = p.name

    with open(p, "r") as f:
        program_src = f.read().strip()

    if main:
        code_css = "#main-program-code"
    else:  # aux program
        code_css = ".aux-program-code"  # can be more than one

    program_repo_rel_path = p.relative_to(ROOT).as_posix()

    sep = '<span class="program-code-link-sep">|</span>'

    s = f"""
<details>
  <summary markdown="span">
    `{program_name}`
    {sep}
    [View on GitHub {{% octicon mark-github %}}]({REPO_ROOT_URL_FOR_LINKS}/{program_repo_rel_path})
  </summary>

```matlab
{program_src}
```
{{: {code_css}}}

</details>
    """.strip()

    return s


def _count_lines(file):
    count = 0
    for _ in file.readlines():
        count += 1

    return count


def _count_lines_s(s):
    return len(s.split("\n"))


def md_text_output(p):
    """Create markdown for a toggler to show given output file.

    p : Path
        to the file

    """

    file_name = p.name

    with open(p, "r") as f:
        # file_line_count = _count_lines(f)  # < need to reset to beginning after this
        file_contents = f.read().strip()

    file_line_count = _count_lines_s(file_contents)

    # detect if it is the standard output file
    if file_name[:3] == "sp_" and file_name[-8:] == "_out.txt":
        stdout = True
    else:
        stdout = False

    if stdout:
        file_note = " (standard output)"
    else:
        file_note = ""

    code_css = ".main-program-output-text-file"

    # TODO: a lot in here is repeated from the matlab program one

    file_repo_rel_path = p.relative_to(ROOT).as_posix()

    sep = '<span class="program-code-link-sep">|</span>'


    # TODO: GH also has a size limit for what it will show in the normal browser
    # should not put the link for those that are too big
    if file_line_count <= 200:

        s = f"""
<details>
  <summary markdown="span">
    `{file_name}`{file_note}
    {sep}
    [View on GitHub {{% octicon mark-github %}}]({REPO_ROOT_URL_FOR_LINKS}/{file_repo_rel_path})
    {sep}
    [View raw]({REPO_ROOT_URL_FOR_RAW_LINKS}/{file_repo_rel_path})
  </summary>

```
{file_contents}
```
{{: {code_css}}}

</details>
        """.strip()

    else:  # file too long. don't actually put it in there.

        s = f"""
<span class="main-program-output-text-file-links-only">
  `{file_name}`{file_note}
  {sep}
  [View on GitHub {{% octicon mark-github %}}]({REPO_ROOT_URL_FOR_LINKS}/{file_repo_rel_path})
  {sep}
  [View raw]({REPO_ROOT_URL_FOR_RAW_LINKS}/{file_repo_rel_path})
</span>
        """.strip()

    return s



def md_text_outputs(sp_id):
    """For sp_id, search for output text files and generate md."""

    # TODO: add fn to get the matlab programs as dict with sp_id keys. and use that the other places as well
    dirs = get_matlab_program_dirs()
    keys = [p.stem for p in dirs]
    dir_ = dict(zip(keys, dirs))[sp_id]

    # anything that isn't .m or .png *should* be an output (.txt or .dat)
    all_files = list(dir_.glob("*"))
    # print(all_files)
    exclude = (".m", ".png")
    files = [p for p in all_files if p.suffix not in exclude]
    # print(files)
    assert all(suff in (".txt", ".dat") for suff in set(p.suffix for p in files))

    header = "## Text"

    if files:
        s_files = []
        for i, file in enumerate(sorted(files)):
            s_files.append(md_text_output(file))

        # return "\n\n".join([header] + s_files)
        return "\n".join([header] + s_files)

    else:
        return ""



def md_figure(p, num=None):
    """Generate md snippet for given figure path."""
    if num is None:
        num = "X"

    # TODO: possibly soft-link the outputs to a location in /docs instead
    p_rr = p.relative_to(ROOT).as_posix()
    url = f"{REPO_ROOT_URL_FOR_RAW_LINKS}/{p_rr}"

    s = f"""
Figure {num}

<img src="{url}">

    """.strip()

    return s


def md_figures(sp_id):
    """For sp_id, search for output figures and generate md."""

    # TODO: add fn to get the matlab programs as dict with sp_id keys. and use that the other places as well
    dirs = get_matlab_program_dirs()
    keys = [p.stem for p in dirs]
    dir_ = dict(zip(keys, dirs))[sp_id]

    figs = list(dir_.glob("*.png"))

    header = "## Figures"

    if figs:

        s_figs = []
        for i, fig in enumerate(sorted(figs)):
            s_figs.append(md_figure(fig, num=i+1))

        return "\n\n".join([header] + s_figs)

    else:

        return ""



def get_matlab_program_dirs():

    folders = ROOT.glob('./sp_??_??')
    return list(folders)
    # return [p.stem for p in folders]


def load_matlab_src_paths():

    script_folders = list(get_matlab_program_dirs())
    # needs to be list for zip to work apparently

    # construct dict
    keys = [p.stem for p in script_folders]

    data = {}
    for k, p in zip(keys, script_folders):
        main_program = list(p.glob("./sp_??_??.m"))[0]
        aux_programs = sorted(
            [p for p in p.glob("./*.m") if p != main_program],
            key=lambda p: p.stem.lower()
        )
        # ^ we sort these case-agnostic alphabetical to avoid annoying diffs
        data[k] = {
            'main_program': main_program,
            'aux_programs': aux_programs,
        }

    return data


def load_data():

    with open("data.yml", "r") as f:
        data = yaml.load(f, Loader=yaml.Loader)

    # construct chapter title lookup
    # with chapter number (int) as key
    # chapter_titles = {d["number"]: d["title"] for d in data["book_chapters"]}
    chapter_titles = {
        d["number"]: f"{d['number']}. {d['title']}"
        for d in data["book_chapters"]
    }

    # check that list of programs match with the matlab scripts
    script_folders = get_matlab_program_dirs()
    ids0 = [p.stem for p in script_folders]
    ids = [d['id'] for d in data['supplemental_programs']]
    assert len(ids0) == len(ids)
    assert all( id0 in ids for id0 in ids0 )

    # reorganize as a dict with sp id's as keys ("deserialize"?)
    #   each value is a dict that we can dump to the header
    # maybe pyyaml has options to load this way automatically?

    sp_data = {}
    for d in data['supplemental_programs']:
        
        id_ = d["id"]
        title = d["title"]

        # extract chapter num and sp num
        nums = id_[3:].split("_")
        chapter_num = int(nums[0])
        sp_num = int(nums[1])
        # or could use https://github.com/r1chardj0n3s/parse

        sp_data[id_] = {
            "chapter_num": chapter_num,
            "chapter_title": chapter_titles[chapter_num],
            "sp_num": sp_num,
            "sp_title": title,
            "sp_id": id_,
            "sp_id_book": f"{chapter_num}.{sp_num}", 
        }

    return chapter_titles, sp_data


def run_matlab_scripts(matlab_src_paths, *, 
    save_figs=True,
):
    """Use matlab.engine to run the Matlab scripts and save the outputs.

    matlab_src_paths : dict
        of dicts with keys ["main_program", "aux_programs"]
        created by fn `load_matlab_src_paths`
    
    save_figs : bool
        we can avoid annoying diffs by not re-saving the figs
        (if we don't expect changes in them)
        
    """

    # TODO: more informative run log
    # matlab version, date/time start/finish, status for each program,
    # so can link to that on the page

    # start matlab
    # `-nodisplay` by default. this warning when saving figs:
    # Warning: MATLAB cannot use OpenGL for printing when started with the '-nodisplay' option.
    # and the figs look a bit different (not as good)
    import matlab.engine  # pylint: disable=import-error
    #eng = matlab.engine.start_matlab()
    eng = matlab.engine.start_matlab("-desktop")  # only works if X forwarding enabled and working

    # we will use StringIO buffers to catch Matlab text output
    import io

    # must be able to find our `save_open_figs` fn on the search path
    eng.addpath("./")

    # too lazy to use logging
    import datetime
    import time
    s_run_log = f"""
Run log
=======

begin: {datetime.datetime.now()}

    """
    # TODO: change to open log file here and write along the way so can watch progress

    # for sp_id, d in sorted(matlab_src_paths.items()): 
    for _, d in sorted(matlab_src_paths.items()): 
        p_main_program = d["main_program"]
        dir_main_program = p_main_program.parent        
        main_program = p_main_program.stem  # to run in matlab, no ext

        s_run_log += f"""
{main_program}
--------
        """

        # start count
        start_i = time.perf_counter()

        # preprare to catch messages in the Matlab command window
        out = io.StringIO()
        err = io.StringIO()
        
        # call the main program script

        # change directory
        # because some of the programs write output files to the cwd
        #os.chdir(dir_main_program)  # note requires py36+
        s_dir_main_program = dir_main_program.as_posix()  # matlab always uses /
        eng.cd(s_dir_main_program)         
   
        # close open figures before running
        # else the previous fig gets saved again in the new dir when a program fails or a program doesn't produce a fig
        eng.close("all")
        eng.clear(nargout=0)  # clear workspace variables from previous run
    
        to_call = getattr(eng, main_program)
        try:
            # ret = to_call(nargout=0, stdout=out, stderr=err)
            to_call(nargout=0, stdout=out, stderr=err)
            s_run_log += f"\nsuccess: true\n"
        except matlab.engine.MatlabExecutionError as e:
            #print(f"{main_program} failed, with error:\n{e}")
            s_run_log +=f"\nsuccess: false\n"
            s_run_log += f"error:\n{e}"

        #print(ret)
        #print(out.read())
        #print(err.read())

        # save messages if they exist
        # .getvalue() gives the whole thing, but a copy
        if out.getvalue().strip():
            with open(dir_main_program / f"{main_program}_out.txt", "w") as f:
                out.seek(0)
                shutil.copyfileobj(out, f)
        if err.getvalue().strip():
            with open(dir_main_program / f"{main_program}_err.txt", "w") as f:
                err.seek(0)
                shutil.copyfileobj(err, f)

        # save any open figures
        eng.delete("*.png", nargout=0)  # ensure only the ones that belong are saved here
        if save_figs:
            eng.save_open_figs(s_dir_main_program, nargout=0)

        # check for new files created
        # and change names if necessary?
        # or we can assume that any new files that don't follow these^ conventions
        # or are .m files are new, products of the program
   
        # close buffers
        #print(out.getvalue())
        #print(err.getvalue())
        out.close()
        err.close()
 
        # log time it took to complete
        elapsed_i = time.perf_counter() - start_i
        s_run_log += f"\ntime: {elapsed_i:.1f} s\n\n"


    # close the engine 
    eng.exit()

    # write log
    s_run_log += f"\nend: {datetime.datetime.now()}\n\n"
    with open("matlab_run_log.txt", "w") as f:
        f.write(s_run_log)
    # this way we avoid getting the annoying UndocumentedMatlab HTML message in the log


def create_md(sp_data, matlab_src_data):
    """Create a md file from the template.
    
    PARAMS
    ------
    sp_data : dict
        metadata
    
    matlab_src_data : dict
        main_program, 

    RETURNS
    -------
    string of the file to be written

    """
    # note: only main program for now
    # TODO: would be better if the two dicts were one!

    yaml_main_metadata = yaml.dump(sp_data)

    # in the header put *repo-relative* paths for the matlab programs
    # main program as single value, aux program(s) as array
    p_main = matlab_src_data["main_program"].relative_to(ROOT)
    p_aux_list = [p.relative_to(ROOT) for p in matlab_src_data["aux_programs"]]
    sp_dir = p_main.parent
    yaml_files = yaml.dump({
        "main_program_repo_rel_path": f"{sp_dir}/{p_main.name}",
        "aux_program_repo_rel_paths": [f"{sp_dir}/{p.name}" for p in p_aux_list],
    })

    # Jekyll parameters (https://jekyllrb.com/docs/front-matter/; in addition to title)
    permalink = f"/ch{sp_data['chapter_num']:02d}/{sp_data['sp_num']:02d}.html"
    title = f"Supplemental Program {sp_data['sp_id_book']}"
    yaml_jekyll = yaml.dump({
        "permalink": permalink,
        "title": title,
    })

    # Just-the-docs parameters
    # https://pmarsceill.github.io/just-the-docs/docs/navigation-structure/
    yaml_jtd = yaml.dump({
        # "nav_order": 2,
        "parent": sp_data["chapter_title"],
    })


    # # main program Matlab source code
    # with open(matlab_src_data["main_program"], "r") as f:
    #     main_program_src = f.read().strip()

    # combine YAMLs
    yaml_note = "# note: this file is automatically generated!"
    yamls = [yaml_main_metadata, yaml_files, yaml_jekyll, yaml_jtd]
    yaml_header_data = "# \n".join(yamls).rstrip()
    yaml_header = "\n".join([yaml_note, yaml_header_data])
    # TODO: instead of just `# `, have `# header` for each YAML section?

    # # use the format to create the str
    # s = PROGRAM_PAGE_MD_FORMAT.format(
    #     yaml_header=yaml_header,
    #     main_program_src=main_program_src,
    #     main_program_name=f"{sp_id}.m",
    # )

    # create Matlab program md snippets
    md_main_program = md_matlab_program(matlab_src_data["main_program"])

    if matlab_src_data["aux_programs"]:
        md_aux_programs = "## Aux. programs\n\n" + "\n\n".join([
            md_matlab_program(p, main=False)
            for p in matlab_src_data["aux_programs"]
        ])
    else:
        md_aux_programs = ""

    # figures
    figures = md_figures(sp_data["sp_id"])

    # outputs
    outputs = md_text_outputs(sp_data["sp_id"])
    # print(outputs)

#     # hardcode hack for now
#     last_failed = [
#         "sp_07_01", 
#         "sp_11_01",
#         "sp_12_01",
#         "sp_12_02",
#         "sp_13_01",
#         "sp_14_03",
#         "sp_16_01",
#     ]
#     if sp_data["sp_id"] in last_failed:
#         figures = """
# Running the program failed.

# # See [the run log](https://github.com/zmoon92/bonanmodeling/blob/gh-pages-dev/gen_md/matlab_run_log.txt).

# #         """.strip()


    # put in 
    #  1. toc
    #  {{:toc}}
    # at top to get auto-generated TOC

    # create the str here so we can use f-string
    s = f"""
---
{yaml_header}
---

# Code

## Main program

{md_main_program}

{md_aux_programs}

# Output

{figures}

{outputs}

    """.strip()


    return s


def write_md(sp_id, s, parent_dir=None):
    """Write md file str `s` to file."""

    # parent_dir is relative to md out root
    if parent_dir is None:
        parent_dir = MD_OUT_ROOT
    else: 
        parent_dir = MD_OUT_ROOT / Path(parent_dir)  # note: creates a new obj if already Path


    parent_dir.mkdir(exist_ok=True)  # create if necessary

    p = parent_dir / f"{sp_id}.md"
    with open(p, "w") as f:
        f.write(s)


def chapter_pages(chapter_titles):
    """Create the chapter pages."""
    # TODO: add descriptions from http://www.cgd.ucar.edu/staff/bonan/ecomod/index.html?

    for i, (num, title) in enumerate(sorted(chapter_titles.items())):

        # hack for now
        if title[1] == "." or title[2] == ".":
            real_title = title[title.index(".")+2:]
        else:
            real_title = title
        
        ch_id = f"{num:02d}"

        s = f"""
---
title: {title}
permalink: /{ch_id}/
nav_order: {i}
has_children: True
---

This is a chapter page for:  
Chapter {num} -- {real_title}

        """.strip()

        with open(MD_OUT_ROOT / f"ch{ch_id}.md", "w") as f:
            f.write(s)



def run_matlab_script(sp_id, matlab_src_paths, #*,
    # **kwargs
):
    """Run selected program(s) only, for testing purposes.
    
    sp_id : str or list(str)
        sp_id's to run


    **kwargs passed on to `run_matlab_scripts()`

    """

    if isinstance(sp_id, str):
        sp_id_run = [sp_id]
    elif isinstance(sp_id, list):
        sp_id_run = sp_id[:]
    else:
        raise TypeError(f"`sp_id` should be str or list")

    matlab_src_paths_run = {
        k: v
        for k, v in matlab_src_paths.items()
        if k in sp_id_run
    }

    run_matlab_scripts(matlab_src_paths_run)




if __name__ == "__main__":

    matlab_srcs = load_matlab_src_paths()

    chapter_titles, sp_data = load_data()

    #> test on one main program
    # sp_id_test = "sp_14_03"  # has aux files

    # run_matlab_script(sp_id_test, matlab_srcs)

    # s = create_md(sp_data[sp_id_test], matlab_srcs[sp_id_test])
    # write_md(sp_id_test, s)
    # write_md(sp_id_test, s, parent_dir="ch14")

    #> run all matlab scripts
    #  note `save_figs=False` is an option now
    # run_matlab_scripts(matlab_srcs)

    #> create and write chapter pages
    # chapter_pages(chapter_titles)

    #> create and write all md for program pages
    for sp_id, sp_data_id in sp_data.items():
        ch_id = f"ch{sp_data_id['chapter_num']:02d}"
        s = create_md(sp_data_id, matlab_srcs[sp_id])
        # p = Path(ch_id)
        # p.mkdir(exist_ok=True)
        # write_md(sp_id, s, parent_dir=p)
        write_md(sp_id, s)



