def current_context():
  return {
    "@context": {
      "obi": "http://standard.openbadges.org/#",
      "assertion": "obi:Assertion",
      "badgeclass": "obi:BadgeClass",
      "issuerorg": "obi:Issuer",
      "extension": "http://openbadges.org/extensions#",
      "xsd": "http://www.w3.org/2001/XMLSchema#",
      "schema": "http://schema.org/",

      "name": { "@id": "schema:name", "@type": "xsd:string" },
      "description": { "@id": "schema:description", "@type": "xsd:string" },
      "type": { "@id": "obi:type", "type": "xsd:string" },
      "url": { "@id": "schema:url", "@type": "@id" },
      "image": { "@id": "obi:image", "@type": "@id" },

      "uid": { "@id": "assertion:Uid", "type": "xsd:string" },
      "recipient": { "@id": "assertion:Recipient", "type": "@id" },
      "hashed": { "@id": "obi:hashed", "type": "xsd:boolean" },
      "salt": { "@id": "obi:salt", "@type": "xsd:string" },
      "identity": { "@id": "obi:identityHash", "@type": "@id" },
      "issuedOn": { "@id": "assertion:IssueDate", "@type": "xsd:dateTime" },
      "expires": { "@id": "assertion:ExpirationDate", "@type": "xsd:dateTime" },
      "evidence": { "@id": "assertion:Evidence", "@type": "@id" },
      "verify": { "@id": "assertion:VerificationObject", "@type": "@id" },

      "badge": { "@id": "badgeclass", "@type": "@id" },
      "criteria": { "@id": "badgeclass:Criteria", "@type": "@id" },
      "tags": { "@id": "badgeclass:Tags", "@type": "@id" },
      "alignment": { "@id": "badgeclass:Alignment", "@type": "@id" },

      "issuer": { "@id": "issuerorg", "@type": "@id" },
      "email": { "@id": "schema:email", "@type": "@id" },
      "revocationList": { "@id": "issuerorg:RecovationList", "@type": "@id" }

    },
    "obi:validation": [
      {
        "obi:validatesType": "assertion",
        "obi:validationSchema": "http://localhost:8000/static/1.1/schema/assertion"
      },
      {
        "obi:validatesType": "badgeclass",
        "obi:validationSchema": "http://localhost:8000/static/1.1/schema/badgeclass"
      },
      {
        "obi:validatesType": "issuerorg",
        "obi:validationSchema": "http://localhost:8000/static/1.1/schema/issuer"
      },
      {
        "obi:validatesType": "extension",
        "obi:validationSchema": "http://localhost:8000/static/1.1/schema/extension"
      }
    ]
  }
