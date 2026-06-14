import httpx

async def get_card_info(bin_number: str) -> dict:
    """
    Отримує інформацію про картку за BIN (перші 6 цифр).
    Використовує безкоштовний API binlist.net
    """
    # Беремо тільки перші 6 цифр
    bin_prefix = bin_number[:6]
    url = f"https://lookup.binlist.net/{bin_prefix}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url)
            
            if response.status_code == 404:
                return {"error": f"BIN {bin_prefix} not found"}
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "bin": bin_prefix,
                "brand": data.get("scheme", "N/A"),
                "bank": data.get("bank", {}).get("name", "N/A"),
                "country": data.get("country", {}).get("name", "N/A"),
                "country_code": data.get("country", {}).get("alpha2", "N/A"),
                "card_type": data.get("type", "N/A"),
                "card_level": data.get("brand", "N/A")
            }
        except Exception as e:
            return {"error": str(e)}
