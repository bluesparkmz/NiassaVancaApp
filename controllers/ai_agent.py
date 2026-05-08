"""
AI Agent for querying company and product information.
This module provides tools for the AI to access database information.
"""
import re
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

import models


def _value(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if value is None:
        return None
    return str(value)


def _clean_query(message: str) -> str:
    text = re.sub(r"[^\w\sÀ-ÿ-]", " ", message.lower())
    stopwords = {
        "quero", "procurar", "procura", "pesquisa", "pesquisar", "mostra", "mostrar", "sobre",
        "empresa", "empresas", "produto", "produtos", "hotel", "restaurante", "alojamento",
        "em", "na", "no", "de", "da", "do", "dos", "das", "o", "a", "os", "as", "um", "uma",
        "me", "diz", "fala", "info", "informacao", "informação", "contacto", "contactos",
    }
    words = [word for word in text.split() if len(word) > 2 and word not in stopwords]
    return " ".join(words[:8]).strip()


def find_company(db: Session, identifier: str | int) -> Optional[models.Company]:
    q = db.query(models.Company).filter(models.Company.status == models.CompanyStatus.APPROVED)
    if isinstance(identifier, int) or str(identifier).isdigit():
        company = q.filter(models.Company.id == int(identifier)).first()
        if company:
            return company
    text = str(identifier).strip()
    if not text:
        return None
    slug = text.lower().replace(" ", "-")
    company = q.filter(or_(models.Company.slug == slug, models.Company.name.ilike(text))).first()
    if company:
        return company
    return q.filter(models.Company.name.ilike(f"%{text}%")).first()


def search_companies(
    db: Session,
    query: str,
    company_type: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Search for companies by name, type, or location.
    """
    print(f"[AI Agent] search_companies called with query={query}, company_type={company_type}, location={location}, limit={limit}")
    
    q = db.query(models.Company).filter(
        models.Company.status == models.CompanyStatus.APPROVED
    )

    if query:
        q = q.filter(
            or_(
                models.Company.name.ilike(f"%{query}%"),
                models.Company.description.ilike(f"%{query}%"),
                models.Company.location.ilike(f"%{query}%"),
            )
        )

    if company_type:
        q = q.filter(models.Company.company_type == company_type)

    if location:
        q = q.filter(
            or_(
                models.Company.location.ilike(f"%{location}%"),
                models.Company.district.ilike(f"%{location}%"),
            )
        )

    results = q.limit(limit).all()
    print(f"[AI Agent] search_companies found {len(results)} results")
    return [_company_to_dict(c) for c in results]


def get_company_details(db: Session, company_id: int | str) -> Optional[dict[str, Any]]:
    """
    Get detailed information about a specific company.
    """
    company = find_company(db, company_id)
    if not company:
        return None
    return _company_to_dict(company, detailed=True)


def search_site(db: Session, query: str, limit: int = 8) -> dict[str, Any]:
    cleaned = _clean_query(query) or query.strip()
    return {
        "query": cleaned,
        "companies": search_companies(db, cleaned, limit=limit),
        "products": search_products(db, cleaned, limit=limit),
        "services": search_services(db, cleaned, limit=limit),
    }


def search_lodgings(
    db: Session, query: str, location: Optional[str] = None, limit: int = 5
) -> list[dict[str, Any]]:
    """
    Search for lodging companies (hotels, apartments, etc).
    """
    q = db.query(models.Company).filter(
        and_(
            models.Company.company_type.in_(
                [
                    models.CompanyType.HOTEL.value,
                    models.CompanyType.LODGING.value,
                    models.CompanyType.HOSPITALITY.value,
                    models.CompanyType.BEACH.value,
                    models.CompanyType.RESTAURANT_RESIDENCE.value,
                ]
            ),
            models.Company.status == models.CompanyStatus.APPROVED,
        )
    )

    if query:
        q = q.filter(
            or_(
                models.Company.name.ilike(f"%{query}%"),
                models.Company.description.ilike(f"%{query}%"),
            )
        )

    if location:
        q = q.filter(
            or_(
                models.Company.location.ilike(f"%{location}%"),
                models.Company.district.ilike(f"%{location}%"),
            )
        )

    results = q.limit(limit).all()
    return [_company_to_dict(c) for c in results]


def search_restaurants(
    db: Session, query: str, location: Optional[str] = None, limit: int = 5
) -> list[dict[str, Any]]:
    """
    Search for restaurant companies.
    """
    q = db.query(models.Company).filter(
        and_(
            models.Company.company_type.in_(
                [
                    models.CompanyType.RESTAURANT.value,
                    models.CompanyType.HOTEL.value,
                ]
            ),
            models.Company.status == models.CompanyStatus.APPROVED,
        )
    )

    if query:
        q = q.filter(
            or_(
                models.Company.name.ilike(f"%{query}%"),
                models.Company.description.ilike(f"%{query}%"),
            )
        )

    if location:
        q = q.filter(
            or_(
                models.Company.location.ilike(f"%{location}%"),
                models.Company.district.ilike(f"%{location}%"),
            )
        )

    results = q.limit(limit).all()
    return [_company_to_dict(c) for c in results]


def search_experiences(
    db: Session, query: str, location: Optional[str] = None, limit: int = 5
) -> list[dict[str, Any]]:
    """
    Search for experience companies (tours, activities, etc).
    """
    q = db.query(models.Company).filter(
        and_(
            models.Company.company_type.in_(
                [
                    models.CompanyType.EXPERIENCE.value,
                    models.CompanyType.TRAVEL_AGENCY.value,
                ]
            ),
            models.Company.status == models.CompanyStatus.APPROVED,
        )
    )

    if query:
        q = q.filter(
            or_(
                models.Company.name.ilike(f"%{query}%"),
                models.Company.description.ilike(f"%{query}%"),
            )
        )

    if location:
        q = q.filter(
            or_(
                models.Company.location.ilike(f"%{location}%"),
                models.Company.district.ilike(f"%{location}%"),
            )
        )

    results = q.limit(limit).all()
    return [_company_to_dict(c) for c in results]


def search_producers(
    db: Session, query: str, location: Optional[str] = None, limit: int = 5
) -> list[dict[str, Any]]:
    """
    Search for producer companies (farms, suppliers, etc).
    """
    q = db.query(models.Company).filter(
        and_(
            models.Company.company_type.in_(
                [
                    models.CompanyType.PRODUCER.value,
                    models.CompanyType.SUPPLIER.value,
                    models.CompanyType.GOODS_SUPPLIER.value,
                    models.CompanyType.AGRO_LIVESTOCK.value,
                ]
            ),
            models.Company.status == models.CompanyStatus.APPROVED,
        )
    )

    if query:
        q = q.filter(
            or_(
                models.Company.name.ilike(f"%{query}%"),
                models.Company.description.ilike(f"%{query}%"),
            )
        )

    if location:
        q = q.filter(
            or_(
                models.Company.location.ilike(f"%{location}%"),
                models.Company.district.ilike(f"%{location}%"),
            )
        )

    results = q.limit(limit).all()
    return [_company_to_dict(c) for c in results]


def search_products(
    db: Session, query: str, category: Optional[str] = None, limit: int = 5
) -> list[dict[str, Any]]:
    """
    Search for products in the market (from producers).
    """
    q = (
        db.query(models.ProducerProduct)
        .join(models.ProducerProfile)
        .join(models.Company)
        .filter(
            models.Company.status == models.CompanyStatus.APPROVED,
            models.ProducerProduct.active == True,
        )
    )

    if query:
        q = q.filter(
            models.ProducerProduct.name.ilike(f"%{query}%")
            | models.ProducerProduct.short_description.ilike(f"%{query}%")
        )

    if category:
        q = q.filter(models.ProducerProduct.category.ilike(f"%{category}%"))

    results = q.limit(limit).all()
    return [_product_to_dict(p) for p in results]


def search_services(db: Session, query: str, category: Optional[str] = None, limit: int = 5) -> list[dict[str, Any]]:
    q = (
        db.query(models.CompanyService)
        .join(models.Company)
        .filter(
            models.Company.status == models.CompanyStatus.APPROVED,
            models.CompanyService.active == True,
        )
    )
    if query:
        q = q.filter(
            or_(
                models.CompanyService.name.ilike(f"%{query}%"),
                models.CompanyService.short_description.ilike(f"%{query}%"),
                models.CompanyService.category.ilike(f"%{query}%"),
                models.Company.name.ilike(f"%{query}%"),
            )
        )
    if category:
        q = q.filter(models.CompanyService.category.ilike(f"%{category}%"))
    return [_service_to_dict(item) for item in q.limit(limit).all()]


def get_company_stats(db: Session) -> dict[str, Any]:
    """
    Get statistics about companies and products.
    """
    total_companies = (
        db.query(func.count(models.Company.id))
        .filter(models.Company.status == models.CompanyStatus.APPROVED)
        .scalar()
    )

    companies_by_type = (
        db.query(
            models.Company.company_type, func.count(models.Company.id).label("count")
        )
        .filter(models.Company.status == models.CompanyStatus.APPROVED)
        .group_by(models.Company.company_type)
        .all()
    )

    return {
        "total_companies": total_companies,
        "by_type": {
            str(ct).split(".")[-1] if hasattr(ct, "__class__") else ct: count
            for ct, count in companies_by_type
        },
    }


def _company_to_dict(company: models.Company, detailed: bool = False) -> dict[str, Any]:
    """Convert a Company model to a dictionary."""
    data = {
        "id": company.id,
        "name": company.name,
        "slug": company.slug,
        "type": _value(company.company_type),
        "category": company.category,
        "location": company.location,
        "district": company.district,
        "short_description": company.short_description,
        "description": company.description,
        "phone": company.phone,
        "email": company.email,
        "whatsapp": company.whatsapp,
        "website": company.website,
        "instagram": company.instagram,
        "facebook": company.facebook,
        "verified": company.is_verified,
        "featured": company.is_featured,
    }
    if not detailed:
        data["description"] = company.short_description or company.description
        return data

    data["gallery_images"] = list(company.gallery_images or [])[:8]
    data["services"] = [_service_to_dict(item) for item in company.services if item.active][:10]
    if company.producer_profile:
        data["producer_profile"] = {
            "area": company.producer_profile.area,
            "rating": str(company.producer_profile.rating) if company.producer_profile.rating is not None else None,
            "sales_count": company.producer_profile.sales_count,
            "story_quote": company.producer_profile.story_quote,
            "social_links": company.producer_profile.social_links or [],
        }
        data["products"] = [_product_to_dict(item) for item in company.producer_profile.products if item.active][:10]
    if company.lodging_profile:
        data["lodging_profile"] = {
            "stay_type": company.lodging_profile.stay_type,
            "price_per_night": str(company.lodging_profile.price_per_night),
            "currency": company.lodging_profile.currency,
            "rating": str(company.lodging_profile.rating) if company.lodging_profile.rating is not None else None,
            "amenities": company.lodging_profile.amenities or [],
            "check_in_time": company.lodging_profile.check_in_time,
            "check_out_time": company.lodging_profile.check_out_time,
            "rooms": [_room_to_dict(item) for item in company.lodging_profile.rooms if item.active][:10],
        }
    if company.restaurant_profile:
        data["restaurant_profile"] = {
            "cuisine": company.restaurant_profile.cuisine,
            "signature": company.restaurant_profile.signature,
            "rating": str(company.restaurant_profile.rating) if company.restaurant_profile.rating is not None else None,
            "menu_items": list(company.restaurant_profile.menu_items or [])[:20],
            "gallery_images": list(company.restaurant_profile.gallery_images or [])[:8],
        }
    if company.experience_profile:
        data["experience_profile"] = {
            "host_name": company.experience_profile.host_name,
            "schedule_text": company.experience_profile.schedule_text,
            "badge": company.experience_profile.badge,
            "category_label": company.experience_profile.category_label,
        }
    return data


def _product_to_dict(product: models.ProducerProduct) -> dict[str, Any]:
    """Convert a ProducerProduct model to a dictionary."""
    producer_name = None
    try:
        if product.producer and hasattr(product.producer, 'company') and product.producer.company:
            producer_name = product.producer.company.name
    except Exception:
        pass
    
    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "producer_id": product.producer_id,
        "producer_name": producer_name,
        "price": str(product.price_amount) if product.price_amount else product.price_label,
        "category": product.category,
        "description": product.short_description,
        "image": product.image_url,
    }


def _service_to_dict(service: models.CompanyService) -> dict[str, Any]:
    return {
        "id": service.id,
        "name": service.name,
        "company_id": service.company_id,
        "company_name": service.company.name if service.company else None,
        "price": str(service.price_amount) if service.price_amount else service.price_label,
        "category": service.category,
        "description": service.short_description,
        "image": service.image_url,
    }


def _room_to_dict(room: models.LodgingRoom) -> dict[str, Any]:
    return {
        "id": room.id,
        "name": room.name,
        "room_type": room.room_type,
        "capacity": room.capacity,
        "price_per_night": str(room.price_per_night),
        "currency": room.currency,
        "total_units": room.total_units,
        "amenities": room.amenities or [],
        "description": room.short_description,
    }


def extract_company_reference(message: str) -> Optional[str]:
    patterns = [
        r"empresa chamada ([\w\sÀ-ÿ'-]+)",
        r"empresa ([\w\sÀ-ÿ'-]+)",
        r"sobre ([\w\sÀ-ÿ'-]+)",
        r"contactos? (?:da|de|do) ([\w\sÀ-ÿ'-]+)",
        r"perfil (?:da|de|do) ([\w\sÀ-ÿ'-]+)",
    ]
    lower = message.strip()
    for pattern in patterns:
        match = re.search(pattern, lower, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip(" .?,!")
            if value:
                return value
    return None


def build_agent_context(db: Session, message: str) -> str:
    blocks: list[str] = []
    company_reference = extract_company_reference(message)
    if company_reference:
        company = get_company_details(db, company_reference)
        if company:
            blocks.append("DETALHES_DA_EMPRESA:\n" + _format_json(company))

    intent, params = extract_search_intent(message)
    params["query"] = _clean_query(message) or message
    if intent:
        site_data: dict[str, Any] = {"intent": intent}
        if intent == "lodgings":
            site_data["results"] = search_lodgings(db, params["query"], params.get("location"), limit=6)
        elif intent == "restaurants":
            site_data["results"] = search_restaurants(db, params["query"], params.get("location"), limit=6)
        elif intent == "experiences":
            site_data["results"] = search_experiences(db, params["query"], params.get("location"), limit=6)
        elif intent == "producers":
            site_data["results"] = search_producers(db, params["query"], params.get("location"), limit=6)
        elif intent == "products":
            site_data["results"] = search_products(db, params["query"], limit=8)
        else:
            site_data["results"] = search_companies(db, params["query"], location=params.get("location"), limit=8)
        blocks.append("PESQUISA_NO_SITE:\n" + _format_json(site_data))
    else:
        site_data = search_site(db, message, limit=5)
        if site_data["companies"] or site_data["products"] or site_data["services"]:
            blocks.append("PESQUISA_GERAL_NO_SITE:\n" + _format_json(site_data))

    stats = get_company_stats(db)
    blocks.append("ESTATISTICAS_PUBLICAS:\n" + _format_json(stats))
    return "\n\n".join(blocks)[:12000]


def _format_json(data: Any) -> str:
    import json
    return json.dumps(data, ensure_ascii=False, default=str, indent=2)


def extract_search_intent(message: str) -> tuple[str, dict[str, str]]:
    """
    Extract search intent and parameters from a message.
    Returns: (intent_type, parameters)
    
    intent_types: 'companies', 'lodgings', 'restaurants', 'experiences', 'producers', 'products', None
    """
    lower = message.lower()
    print(f"[AI Agent] Analyzing message: {message}")
    
    # Detect intent patterns - companies first (most general)
    if any(word in lower for word in ["empresa", "negócio", "loja", "estabelecimento", "prestador", "empresas", "negócios", "lojas", "parceiro", "parceiros", "plataforma"]):
        intent = "companies"
        print(f"[AI Agent] Detected intent: companies")
    elif any(word in lower for word in ["hotel", "alojamento", "hospedagem", "acomodação", "pousada", "hostel", "alojamentos", "hotéis", "ficar", "hospedar"]):
        intent = "lodgings"
        print(f"[AI Agent] Detected intent: lodgings")
    elif any(word in lower for word in ["restaurante", "comer", "refeição", "comida", "refeicao", "prato", "prato típico", "comidas", "restaurantes", "café", "cafe"]):
        intent = "restaurants"
        print(f"[AI Agent] Detected intent: restaurants")
    elif any(word in lower for word in ["experiência", "tour", "passeio", "atividade", "viagem", "turismo", "tours", "passeios", "atividades", "experiencias"]):
        intent = "experiences"
        print(f"[AI Agent] Detected intent: experiences")
    elif any(word in lower for word in ["produtor", "agricultor", "fornecedor", "agrícola", "agraria", "produtores", "agricultores", "fornecedores"]):
        intent = "producers"
        print(f"[AI Agent] Detected intent: producers")
    elif any(word in lower for word in ["produto", "mercado", "comprar", "venda", "produto", "produtos", "vender", "vende"]):
        intent = "products"
        print(f"[AI Agent] Detected intent: products")
    else:
        intent = None
        print(f"[AI Agent] No intent detected")
    
    # Extract location if mentioned
    location_patterns = [
        r"em (\w+)",
        r"em (\w+ \w+)",
        r"zona (\w+)",
        r"distrito (\w+)",
        r"na (\w+)",
        r"na (\w+ \w+)",
    ]
    location = None
    for pattern in location_patterns:
        match = re.search(pattern, lower)
        if match:
            location = match.group(1).strip()
            break
    
    parameters = {}
    if location:
        parameters["location"] = location
        print(f"[AI Agent] Extracted location: {location}")
    
    return intent, parameters
