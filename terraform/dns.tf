# --- API Gateway Custom Domain and DNS ---
resource "aws_apigatewayv2_domain_name" "pass_domain_name" {
  domain_name = "pass.lemaire.tel"

  domain_name_configuration {
    certificate_arn = data.aws_acm_certificate.lemaire_tel.arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_apigatewayv2_api_mapping" "pass_api_mapping" {
  api_id      = aws_apigatewayv2_api.pass_api.id
  domain_name = aws_apigatewayv2_domain_name.pass_domain_name.id
  stage       = aws_apigatewayv2_stage.default_stage.id
}

resource "aws_route53_record" "pass_domain_dns" {
  zone_id = "Z042219115MNG2VU6NRK9"
  name    = aws_apigatewayv2_domain_name.pass_domain_name.domain_name
  type    = "A"

  alias {
    name                   = aws_apigatewayv2_domain_name.pass_domain_name.domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.pass_domain_name.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}