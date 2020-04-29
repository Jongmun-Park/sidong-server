import graphene

import art.schema

class Query(art.schema.Query, graphene.ObjectType):
	pass

schema = graphene.Schema(query=Query)
