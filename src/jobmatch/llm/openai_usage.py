from datetime import datetime
from decimal import Decimal
from pathlib import Path
import json


"""
OpenAI API usage tracking for JobMatch.

Purpose:
    This module records and displays OpenAI API token usage and estimated cost.

    It tracks:
    - Input tokens
    - Cached input tokens
    - Cache-write tokens
    - Output tokens
    - Reasoning tokens
    - Total tokens
    - Estimated input/output/total cost
    - Daily cumulative API usage and cost

    Usage records are saved locally to:
        data/usage/openai_usage.json

    Model prices are defined in MODEL_PRICING.
    OpenAI API prices may change, so check PRICING_LAST_VERIFIED before
    relying on the estimated cost.

Usage in other files:
    Import the public tracking function:

        from jobmatch.llm.openai_usage import track_openai_usage

    After receiving an OpenAI API response:

        response = client.responses.create(
            model=MODEL,
            input="..."
        )

        track_openai_usage(
            response=response,
            model=MODEL
        )

Notes:
    - Call track_openai_usage() once for each OpenAI API response that
      should be recorded.
    - Functions beginning with "_" are internal helper functions and
      normally should not be imported by other modules.
    - Calculated costs are estimates based on the pricing stored in this
      module and may differ from the final OpenAI bill.
"""

# ============================================================
# Pricing metadata
# ============================================================

# IMPORTANT:
# OpenAI API prices may change.
# Before relying on these values in the future, verify them
# against the official OpenAI API pricing/model documentation.
PRICING_LAST_VERIFIED = "2026-08-21"

TOKENS_PER_MILLION = Decimal("1000000")


# ============================================================
# Paths
# ============================================================

# Current file:
# project_root/src/jobmatch/llm/openai_usage.py
#
# parents[0] -> llm
# parents[1] -> jobmatch
# parents[2] -> src
# parents[3] -> project root

PROJECT_ROOT = Path(__file__).resolve().parents[3]

USAGE_FILE = (
    PROJECT_ROOT
    / "data"
    / "usage"
    / "openai_usage.json"
)


# ============================================================
# Model pricing
#
# Prices are USD per 1 million tokens.
#
# This table assumes normal API usage.
# It does not include:
# - Web Search tool fees
# - Code Interpreter fees
# - File Search fees
# - image generation fees
# - regional processing surcharges
# - special service tiers
# ============================================================

MODEL_PRICING = {

    # --------------------------------------------------------
    # GPT-5.6 family
    # --------------------------------------------------------

    "gpt-5.6": {
        "input": Decimal("5.00"),
        "cached_input": Decimal("0.50"),
        "cache_write": Decimal("6.25"),
        "output": Decimal("30.00"),
        "long_context_threshold": 272_000,
    },

    "gpt-5.6-sol": {
        "input": Decimal("5.00"),
        "cached_input": Decimal("0.50"),
        "cache_write": Decimal("6.25"),
        "output": Decimal("30.00"),
        "long_context_threshold": 272_000,
    },

    "gpt-5.6-terra": {
        "input": Decimal("2.00"),
        "cached_input": Decimal("0.20"),
        "cache_write": Decimal("2.50"),
        "output": Decimal("12.00"),
        "long_context_threshold": 272_000,
    },

    "gpt-5.6-luna": {
        "input": Decimal("0.20"),
        "cached_input": Decimal("0.02"),
        "cache_write": Decimal("0.25"),
        "output": Decimal("1.20"),
        "long_context_threshold": 272_000,
    },


    # --------------------------------------------------------
    # GPT-5.4 family
    # --------------------------------------------------------

    "gpt-5.4": {
        "input": Decimal("2.50"),
        "cached_input": Decimal("0.25"),
        "cache_write": None,
        "output": Decimal("15.00"),
        "long_context_threshold": 272_000,
    },

    "gpt-5.4-mini": {
        "input": Decimal("0.75"),
        "cached_input": Decimal("0.075"),
        "cache_write": None,
        "output": Decimal("4.50"),
        "long_context_threshold": None,
    },

    "gpt-5.4-nano": {
        "input": Decimal("0.20"),
        "cached_input": Decimal("0.02"),
        "cache_write": None,
        "output": Decimal("1.25"),
        "long_context_threshold": None,
    },
}


# ============================================================
# Long-context pricing
# ============================================================

LONG_CONTEXT_INPUT_MULTIPLIER = Decimal("2.0")
LONG_CONTEXT_OUTPUT_MULTIPLIER = Decimal("1.5")


# ============================================================
# History file functions
# ============================================================

def _load_usage_history():

    if not USAGE_FILE.exists():
        return []

    try:
        with open(
            USAGE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (json.JSONDecodeError, OSError):

        return []


def _save_usage_history(usage_history):

    USAGE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        USAGE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            usage_history,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# Pricing functions
# ============================================================

def _get_model_pricing(model: str):

    if model not in MODEL_PRICING:

        raise ValueError(
            f"No pricing configuration exists for "
            f"OpenAI model '{model}'.\n"
            f"Update MODEL_PRICING in openai_usage.py "
            f"before calculating costs."
        )

    return MODEL_PRICING[model]


# ============================================================
# Extract token usage from OpenAI response
# ============================================================

def _get_usage_details(response):

    usage = response.usage

    if usage is None:

        raise ValueError(
            "OpenAI response does not contain usage information."
        )


    input_tokens = usage.input_tokens or 0
    output_tokens = usage.output_tokens or 0
    total_tokens = usage.total_tokens or 0


    # --------------------------------------------------------
    # Input details
    # --------------------------------------------------------

    cached_tokens = 0
    cache_write_tokens = 0

    input_details = getattr(
        usage,
        "input_tokens_details",
        None
    )

    if input_details is not None:

        cached_tokens = (
            getattr(
                input_details,
                "cached_tokens",
                0
            )
            or 0
        )

        cache_write_tokens = (
            getattr(
                input_details,
                "cache_write_tokens",
                0
            )
            or 0
        )


    # --------------------------------------------------------
    # Output details
    # --------------------------------------------------------

    reasoning_tokens = 0

    output_details = getattr(
        usage,
        "output_tokens_details",
        None
    )

    if output_details is not None:

        reasoning_tokens = (
            getattr(
                output_details,
                "reasoning_tokens",
                0
            )
            or 0
        )


    # input_tokens includes cached tokens.
    #
    # Therefore:
    #
    # regular input
    # = total input
    # - cached input
    # - explicit cache-write tokens

    regular_input_tokens = (
        input_tokens
        - cached_tokens
        - cache_write_tokens
    )

    regular_input_tokens = max(
        regular_input_tokens,
        0
    )


    return {
        "input_tokens": input_tokens,
        "regular_input_tokens": regular_input_tokens,
        "cached_tokens": cached_tokens,
        "cache_write_tokens": cache_write_tokens,

        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,

        "total_tokens": total_tokens,
    }


# ============================================================
# Cost calculation
# ============================================================

def _calculate_cost(
    model: str,
    usage_details: dict
):

    pricing = _get_model_pricing(model)

    input_tokens = usage_details["input_tokens"]

    regular_input_tokens = (
        usage_details["regular_input_tokens"]
    )

    cached_tokens = (
        usage_details["cached_tokens"]
    )

    cache_write_tokens = (
        usage_details["cache_write_tokens"]
    )

    output_tokens = (
        usage_details["output_tokens"]
    )


    # --------------------------------------------------------
    # Determine long-context pricing
    # --------------------------------------------------------

    threshold = pricing["long_context_threshold"]

    long_context = (
        threshold is not None
        and input_tokens > threshold
    )


    if long_context:

        input_multiplier = (
            LONG_CONTEXT_INPUT_MULTIPLIER
        )

        output_multiplier = (
            LONG_CONTEXT_OUTPUT_MULTIPLIER
        )

    else:

        input_multiplier = Decimal("1")
        output_multiplier = Decimal("1")


    # --------------------------------------------------------
    # Regular input
    # --------------------------------------------------------

    regular_input_cost = (

        Decimal(regular_input_tokens)
        / TOKENS_PER_MILLION
        * pricing["input"]
        * input_multiplier
    )


    # --------------------------------------------------------
    # Cached input
    # --------------------------------------------------------

    cached_input_cost = (

        Decimal(cached_tokens)
        / TOKENS_PER_MILLION
        * pricing["cached_input"]
        * input_multiplier
    )


    # --------------------------------------------------------
    # Cache write
    # --------------------------------------------------------

    if (
        cache_write_tokens > 0
        and pricing["cache_write"] is not None
    ):

        cache_write_cost = (

            Decimal(cache_write_tokens)
            / TOKENS_PER_MILLION
            * pricing["cache_write"]
            * input_multiplier
        )

    else:

        cache_write_cost = Decimal("0")


    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    output_cost = (

        Decimal(output_tokens)
        / TOKENS_PER_MILLION
        * pricing["output"]
        * output_multiplier
    )


    # --------------------------------------------------------
    # Totals
    # --------------------------------------------------------

    input_cost = (
        regular_input_cost
        + cached_input_cost
        + cache_write_cost
    )

    total_cost = (
        input_cost
        + output_cost
    )


    return {
        "regular_input_cost": regular_input_cost,
        "cached_input_cost": cached_input_cost,
        "cache_write_cost": cache_write_cost,

        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,

        "long_context": long_context,
    }


# ============================================================
# Decimal -> JSON-safe number
# ============================================================

def _decimal_to_float(value: Decimal):

    return round(
        float(value),
        10
    )


# ============================================================
# Main public function
# ============================================================

def track_openai_usage(
    response,
    model: str
):

    # --------------------------------------------------------
    # Read token usage
    # --------------------------------------------------------

    usage_details = _get_usage_details(
        response
    )


    # --------------------------------------------------------
    # Calculate cost
    # --------------------------------------------------------

    cost_details = _calculate_cost(
        model,
        usage_details
    )


    # --------------------------------------------------------
    # Create usage record
    # --------------------------------------------------------

    now = datetime.now()

    record = {

        "timestamp": now.isoformat(),

        "model": model,

        "pricing_last_verified":
            PRICING_LAST_VERIFIED,


        # Tokens

        "input_tokens":
            usage_details["input_tokens"],

        "regular_input_tokens":
            usage_details["regular_input_tokens"],

        "cached_tokens":
            usage_details["cached_tokens"],

        "cache_write_tokens":
            usage_details["cache_write_tokens"],

        "output_tokens":
            usage_details["output_tokens"],

        "reasoning_tokens":
            usage_details["reasoning_tokens"],

        "total_tokens":
            usage_details["total_tokens"],


        # Costs

        "input_cost":
            _decimal_to_float(
                cost_details["input_cost"]
            ),

        "output_cost":
            _decimal_to_float(
                cost_details["output_cost"]
            ),

        "total_cost":
            _decimal_to_float(
                cost_details["total_cost"]
            ),


        # Pricing mode

        "long_context":
            cost_details["long_context"],
    }


    # --------------------------------------------------------
    # Save history
    # --------------------------------------------------------

    usage_history = _load_usage_history()

    usage_history.append(record)

    _save_usage_history(
        usage_history
    )


    # ========================================================
    # Today's totals
    # ========================================================

    today = now.date().isoformat()

    today_records = [

        item

        for item in usage_history

        if item["timestamp"].startswith(today)
    ]


    today_requests = len(
        today_records
    )


    today_input_tokens = sum(

        item.get(
            "input_tokens",
            0
        )

        for item in today_records
    )


    today_cached_tokens = sum(

        item.get(
            "cached_tokens",
            0
        )

        for item in today_records
    )


    today_cache_write_tokens = sum(

        item.get(
            "cache_write_tokens",
            0
        )

        for item in today_records
    )


    today_output_tokens = sum(

        item.get(
            "output_tokens",
            0
        )

        for item in today_records
    )


    today_reasoning_tokens = sum(

        item.get(
            "reasoning_tokens",
            0
        )

        for item in today_records
    )


    today_total_tokens = sum(

        item.get(
            "total_tokens",
            0
        )

        for item in today_records
    )


    today_input_cost = sum(

        Decimal(
            str(
                item.get(
                    "input_cost",
                    0
                )
            )
        )

        for item in today_records
    )


    today_output_cost = sum(

        Decimal(
            str(
                item.get(
                    "output_cost",
                    0
                )
            )
        )

        for item in today_records
    )


    today_total_cost = sum(

        Decimal(
            str(
                item.get(
                    "total_cost",
                    0
                )
            )
        )

        for item in today_records
    )


    # ========================================================
    # Display
    # ========================================================

    print()
    print("OpenAI API Usage")
    print("────────────────────────────────")

    print(
        f"Pricing verified:   "
        f"{PRICING_LAST_VERIFIED}"
    )

    print(
        f"Model:              "
        f"{model}"
    )


    print()

    print(
        f"Input tokens:       "
        f"{usage_details['input_tokens']:,}"
    )


    if usage_details["cached_tokens"] > 0:

        print(
            f"  Cached input:     "
            f"{usage_details['cached_tokens']:,}"
        )


    if usage_details["cache_write_tokens"] > 0:

        print(
            f"  Cache write:      "
            f"{usage_details['cache_write_tokens']:,}"
        )


    print(
        f"Output tokens:      "
        f"{usage_details['output_tokens']:,}"
    )


    if usage_details["reasoning_tokens"] > 0:

        print(
            f"  Reasoning tokens: "
            f"{usage_details['reasoning_tokens']:,}"
        )


    print(
        f"Total tokens:       "
        f"{usage_details['total_tokens']:,}"
    )


    # --------------------------------------------------------
    # Current request cost
    # --------------------------------------------------------

    print()
    print("This request:")


    print(
        f"Input cost:         "
        f"${cost_details['input_cost']:.6f}"
    )


    print(
        f"Output cost:        "
        f"${cost_details['output_cost']:.6f}"
    )


    print(
        f"Total cost:         "
        f"${cost_details['total_cost']:.6f}"
    )


    if cost_details["long_context"]:

        print(
            "Long-context price: YES"
        )


    # --------------------------------------------------------
    # Today's totals
    # --------------------------------------------------------

    print()
    print("Today:")


    print(
        f"Requests:           "
        f"{today_requests:,}"
    )


    print(
        f"Input tokens:       "
        f"{today_input_tokens:,}"
    )


    if today_cached_tokens > 0:

        print(
            f"Cached input:       "
            f"{today_cached_tokens:,}"
        )


    if today_cache_write_tokens > 0:

        print(
            f"Cache write:        "
            f"{today_cache_write_tokens:,}"
        )


    print(
        f"Output tokens:      "
        f"{today_output_tokens:,}"
    )


    if today_reasoning_tokens > 0:

        print(
            f"Reasoning tokens:   "
            f"{today_reasoning_tokens:,}"
        )


    print(
        f"Total tokens:       "
        f"{today_total_tokens:,}"
    )


    print(
        f"Input cost:         "
        f"${today_input_cost:.6f}"
    )


    print(
        f"Output cost:        "
        f"${today_output_cost:.6f}"
    )


    print(
        f"Total cost:         "
        f"${today_total_cost:.6f}"
    )


    print("────────────────────────────────")


    return record