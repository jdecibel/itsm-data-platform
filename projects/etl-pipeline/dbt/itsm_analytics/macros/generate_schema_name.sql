{#
    dbt's default generate_schema_name concatenates the profile's target
    schema with a model's custom +schema config (e.g. "warehouse_staging").
    We want the plain custom schema name — staging/intermediate/marts, no
    prefix — since those are the exact three schemas provisioned in
    sql/dbt_role.sql. This is the standard override for that behavior.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
