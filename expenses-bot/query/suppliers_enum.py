"""
Enumeración usando la query:

select s.id, s."name" from suppliers s 
where s.supplier_type_id in (
71214,
71215)
and s.suppliers_group_id in (
1,
6992,
8328,
9783)
order by id asc;
"""
SUPPLIERS = {
    "Alphabet": 661167,
    "Arval": 661168,
    "Athlon Car Lease": 661169,
    "Ayvens (ALD Automotive y LeasePlan)": 661170,
    "Europcar": 661171,
    "KINTO (Toyota Fleet Mobility)": 661172,
    "Northgate": 661173,
    "Sabadell Renting": 661174,
    "Santander Renting": 661175,
    "Volkswagen Renting": 661176,
    "Mapfre": 672729,
    "Mutua Madrileña": 672740,
    "Allianz Seguros": 672741,
    "AXA Seguros": 672742,
    "Generali Seguros": 672743,
    "Occident": 672744,
    "Reale Seguros": 672745,
    "Liberty Seguros": 672746,
    "Zurich Seguros": 672747,
    "Linea Directa": 672748,
    "Bansacar": 686303
}
