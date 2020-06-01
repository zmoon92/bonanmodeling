# 
"""
Generate md files from the Matlab scripts. 

"""

# from glob import glob
import os
from pathlib import Path

import yaml


ROOT = Path('../')  # project root. assumes we are running this from this scripts location!

MD_OUT_ROOT = ROOT / "docs/pages"

# to use when creating the links to the source files on GH
# can also use Jekyll github-metadata plugin
REPO_ROOT_URL_FOR_LINKS = "https://github.com/zmoon92/bonanmodeling/tree/master"



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

    program_repo_rel_path = str(p.relative_to(ROOT))

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


def md_figure(p, num=None):
    """Generate md snippet for given figure path."""
    if num is None:
        num = "X"

    # TODO: possibly soft-link the outputs to a location in /docs instead
    # but hack for now
    base_url = "https://raw.githubusercontent.com/zmoon92/bonanmodeling/gh-pages-dev"

    p_rr = p.relative_to(ROOT).as_posix()
    url = f"{base_url}/{p_rr}"

    s = f"""
Figure {num}

<img src="{url}">

    """.strip()

    return s


def md_figures(sp_id):
    """For sp_id, search for output figures and generated md."""

    # TODO: add fn to get the matlab programs as dict with sp_id keys. and use that the other places as well
    dirs = get_matlab_program_dirs()
    keys = [p.stem for p in dirs]
    dir_ = dict(zip(keys, dirs))[sp_id]

    figs = dir_.glob("*.png")

    if figs:

        s_figs = []
        for i, fig in enumerate(sorted(figs)):
            s_figs.append(md_figure(fig, num=i+1))

        return "\n\n".join(s_figs)

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
        aux_programs = [p for p in p.glob("./*.m") if p != main_program] 
        # TODO: sort these ^ e.g. case-agnostic alphabetical 
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


def run_matlab_scripts(matlab_src_paths):
    """Use matlab.engine to run the Matlab scripts and save the outputs.

    matlab_src_paths : dict
        of dicts with keys ["main_program", "aux_programs"]
        created by fn `load_matlab_src_paths`
        
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

    # prepare to catch stdout/err messages
    import io
    out = io.StringIO()
    err = io.StringIO()

    # must be able to find our `save_open_figs` fn on the search path
    eng.addpath("./")

    # for sp_id, d in sorted(matlab_src_paths.items()): 
    for _, d in sorted(matlab_src_paths.items()): 
        p_main_program = d["main_program"]
        dir_main_program = p_main_program.parent        
        main_program = p_main_program.stem  # to run in matlab, no ext

        # addpath so Matlab can find
        eng.addpath(str(dir_main_program))

        # call the main program script

        # change directory
        # because some of the programs write output files to the cwd
        #os.chdir(dir_main_program)  # note requires py36+
        s_dir_main_program = dir_main_program.as_posix()  # matlab always uses /
        eng.cd(s_dir_main_program)         
   
        # TODO: close open figures before running
        # else the previous fig gets saved again in the new dir when a program fails or a program doesn't produce a fig
        eng.close("all")

        to_call = getattr(eng, main_program)
        try:
            # ret = to_call(nargout=0, stdout=out, stderr=err)
            to_call(nargout=0, stdout=out, stderr=err)
        except matlab.engine.MatlabExecutionError as e:
            print(f"{main_program} failed, with error:\n{e}")

        #print(ret)
        #print(out.read())
        #print(err.read())

        # save messages if they exist
        if out.read().strip():
            out.write(dir_main_program / f"{main_program}_out.txt")
        if err.read().strip():
            err.write(dir_main_program / f"{main_program}_err.txt")

        # save any open figures
        eng.delete("*.png")  # ensure only the ones that belong are saved here
        eng.save_open_figs(s_dir_main_program, nargout=0)

        # check for new files created
        # and change names if necessary?
        # or we can assume that any new files that don't follow these^ conventions
        # or are .m files are new, products of the program
    
    # close the engine 
    eng.exit()


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

    # hardcode hack for now
    last_failed = [
        "sp_07_01", 
        "sp_11_01",
        "sp_12_01",
        "sp_12_02",
        "sp_13_01",
        "sp_14_03",
        "sp_16_01",
    ]
    if sp_data["sp_id"] in last_failed:
        figures = """
Running the program failed.

See [the run log](https://github.com/zmoon92/bonanmodeling/blob/gh-pages-dev/gen_md/matlab_run_log.txt).

        """.strip()



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
        
        ch_id = f"{num:02d}"

        s = f"""
---
title: {title}
permalink: /{ch_id}/
nav_order: {i}
has_children: True
---

This is a chapter page.
        """.strip()

        with open(MD_OUT_ROOT / f"ch{ch_id}.md", "w") as f:
            f.write(s)



def run_matlab_script(sp_id, matlab_src_paths):
    """Run selected program(s) only, for testing purposes.
    
    sp_id : str or list(str)
        sp_id's to run
    """

    if isinstance(sp_id, str):
        sp_id_run = [sp_id]

    matlab_src_paths_run = {
        k: v
        for k, v in matlab_src_paths
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

    #> create and write chapter pages
    chapter_pages(chapter_titles)

    #> create and write all md for program pages
    for sp_id, sp_data_id in sp_data.items():
        ch_id = f"ch{sp_data_id['chapter_num']:02d}"
        s = create_md(sp_data_id, matlab_srcs[sp_id])
        # p = Path(ch_id)
        # p.mkdir(exist_ok=True)
        # write_md(sp_id, s, parent_dir=p)
        write_md(sp_id, s)



