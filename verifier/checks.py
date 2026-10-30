"""Checks shared by the tool verifiers. Pure functions of their arguments and the files on disk."""


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def gave_up_verdict(verdict, output):
    """A submission that admits defeat is a failure: invalid with score 0, whatever its attempt was worth.
    The attempt's own score and reasons stay in the details for reference."""
    details = dict(verdict["details"], gave_up=output.gave_up)
    if not output.gave_up:
        return result(verdict["valid"], verdict["message"], score=verdict["score"], **details)
    message = "the agent gave up and admitted it could not solve the puzzle; its attempt: " + verdict["message"]
    return result(False, message, score=0.0, attempt_score=verdict["score"], **details)
