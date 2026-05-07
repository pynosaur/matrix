genrule(
    name = "matrix_bin",
    srcs = glob(["app/**/*.py", "doc/**/*.yaml"]) + [".program"],
    outs = ["matrix"],
    cmd = """
        _VER=$$(grep '^version:' $(location .program) | cut -d' ' -f2)
        /opt/homebrew/bin/nuitka \
            --onefile \
            --include-data-dir=doc=doc \
            --include-data-files=app/*.py=_src/ \
            --include-data-files=app/**/*.py=_src/ \
            --onefile-tempdir-spec=/tmp/nuitka-matrix-$$_VER \
            --no-progressbar \
            --assume-yes-for-downloads \
            --no-deployment-flag=self-execution \
            --output-dir=$$(dirname $(location matrix)) \
            --output-filename=matrix \
            $(location app/main.py)
    """,
    local = 1,
    visibility = ["//visibility:public"],
)
