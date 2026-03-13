# Integration Examples

## Telegram inbound webhook
`POST /api/integrations/telegram/webhook`

```json
{
  "message": {
    "from": { "id": 100200300 },
    "text": "Create task: call me tomorrow at 14:00"
  }
}
```

## WhatsApp inbound webhook
`POST /api/integrations/whatsapp/webhook`

```json
{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messages": [
              { "from": "15551234567", "text": { "body": "Hello" } }
            ]
          }
        }
      ]
    }
  ]
}
```

## Viber inbound webhook
`POST /api/integrations/viber/webhook`

```json
{
  "sender": { "id": "vbr_abc" },
  "message": { "text": "Need a proposal" }
}
```
