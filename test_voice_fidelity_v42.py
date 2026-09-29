from voice_fidelity_v42 import compile_voice_fingerprint, audit_surface_line, epistemic_name_gate

def test_voice_fingerprint_qes():
    bible={"identity":{"identification":"14 anos"},"voice":{"reference_anchor":"Sakura inicial","register":"coloquial-correto","cadence":"expressiva"},"acting":{}}
    fp=compile_voice_fingerprint("Saya Haruno",bible,"Amatsu Uchiha","medium","team")
    assert fp["version"].startswith("v42")
    assert "qes_v42" in fp
    assert "speech_act_fit" in fp["line_review"]

def test_dry_line_review():
    assert "dry_line_review_required" in audit_surface_line("Certo.")

def test_functional_short_can_be_allowed():
    assert "dry_line_review_required" not in audit_surface_line("Recue.",allow_short=True)

def test_modernity_flag():
    assert "modernity_register_review_required" in audit_surface_line("Precisamos otimizar a janela operacional.")

def test_epistemic_name_gate():
    known=["o homem ferido deixou sangue na trilha"]
    assert not epistemic_name_gate("Shuren Kurose",known)
    assert epistemic_name_gate("homem ferido",known)
