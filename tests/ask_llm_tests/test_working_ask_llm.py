import os

import pytest

from ResumeMaker.ask_llm import AskLLM


@pytest.mark.skipif("RUNALL" not in os.environ, reason="takes too long")
def test_ask_llm_working(setup_file):
    script = "A video about a cat. Doing stunts like running around, flying, and jumping."
    ask_llm = AskLLM(config_file=setup_file)
    result = ask_llm.invoke(input_text=script)
    ask_llm.quit_llm()
    assert result["parsed"].title == "Feline Frenzy: Cat Stunt Master!"
    assert (
        result["parsed"].description
        == "Get ready for the most epic feline feats you've ever seen! Watch as our fearless feline friend runs, jumps, and even flies through a series of death-defying stunts."
    )
    assert result["parsed"].tags == ["cat", "stunts", "flying", "jumping"]
    assert (
        result["parsed"].thumbnail_description
        == "A cat in mid-air, performing a daring stunt with its paws outstretched, surrounded by a blurred cityscape with bright lights and colors."
    )
    assert result["parsing_error"] is None
    assert result is not None
