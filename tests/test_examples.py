import io
import pkgutil

import pytest

import altair as alt
from altair.utils.execeval import eval_block
from tests import examples_arguments_syntax
from tests import examples_methods_syntax

try:
    import altair_saver  # noqa: F401
except ImportError:
    altair_saver = None

try:
    import vl_convert as vlc  # noqa: F401
except ImportError:
    vlc = None


def iter_examples_filenames(syntax_module):
    for _importer, modname, ispkg in pkgutil.iter_modules(syntax_module.__path__):
        if ispkg or modname.startswith("_"):
            continue
        yield modname + ".py"


@pytest.mark.parametrize(
    "syntax_module", [examples_arguments_syntax, examples_methods_syntax]
)
def test_render_examples_to_chart(syntax_module):
    for filename in iter_examples_filenames(syntax_module):
        source = pkgutil.get_data(syntax_module.__name__, filename)
        chart = eval_block(source)

        if chart is None:
            raise ValueError(
                f"Example file {filename} should define chart in its final "
                "statement."
            )

        try:
            assert isinstance(chart.to_dict(), dict)
        except Exception as err:
            raise AssertionError(
                f"Example file {filename} raised an exception when "
                f"converting to a dict: {err}"
            ) from err


@pytest.mark.parametrize(
    "syntax_module", [examples_arguments_syntax, examples_methods_syntax]
)
def test_from_and_to_json_roundtrip(syntax_module):
    """Tests if the to_json and from_json (and by extension to_dict and from_dict)
    work for all examples in the Example Gallery.
    """
    for filename in iter_examples_filenames(syntax_module):
        source = pkgutil.get_data(syntax_module.__name__, filename)
        chart = eval_block(source)

        if chart is None:
            raise ValueError(
                f"Example file {filename} should define chart in its final "
                "statement."
            )

        try:
            first_json = chart.to_json()
            reconstructed_chart = alt.Chart.from_json(first_json)
            # As the chart objects are not
            # necessarily the same - they could use different objects to encode the same
            # information - we do not test for equality of the chart objects, but rather
            # for equality of the json strings.
            second_json = reconstructed_chart.to_json()
            assert first_json == second_json
        except Exception as err:
            raise AssertionError(
                f"Example file {filename} raised an exception when "
                f"doing a json conversion roundtrip: {err}"
            ) from err


# We do not apply the save_engine mark to this test. This mark is used in
# the build GitHub Action workflow to select the tests which should be rerun
# with some of the saving engines uninstalled. This would not make sense for this test
# as here it is only interesting to run it with all saving engines installed.
# Furthermore, the runtime of this test is rather long.
@pytest.mark.parametrize("engine", ["vl-convert", "altair_saver"])
@pytest.mark.parametrize(
    "syntax_module", [examples_arguments_syntax, examples_methods_syntax]
)
def test_render_examples_to_png(engine, syntax_module):
    for filename in iter_examples_filenames(syntax_module):
        if engine == "vl-convert" and vlc is None:
            pytest.skip("vl_convert not importable; cannot run mimebundle tests")
        elif engine == "altair_saver":
            if altair_saver is None:
                pytest.skip("altair_saver not importable; cannot run png tests")
            if "png" not in altair_saver.available_formats("vega-lite"):
                pytest.skip("altair_saver not configured to save to png")

        source = pkgutil.get_data(syntax_module.__name__, filename)
        chart = eval_block(source)
        out = io.BytesIO()
        chart.save(out, format="png", engine=engine)
        assert out.getvalue().startswith(b"\x89PNG")
