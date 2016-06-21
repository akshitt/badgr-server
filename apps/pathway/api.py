# Created by wiggins@concentricsky.com on 3/30/16.
from django.conf import settings
from django.core.urlresolvers import resolve, Resolver404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from issuer.api import AbstractIssuerAPIEndpoint
from issuer.models import Issuer, BadgeClass
from mainsite.utils import ObjectView
from pathway.completionspec import CompletionRequirementSpecFactory
from pathway.models import Pathway, PathwayElement, PathwayElementBadge
from pathway.serializers import PathwaySerializer, PathwayListSerializer, PathwayElementSerializer, PathwayElementCompletionSerializer
from recipient.models import RecipientGroup, RecipientProfile


class PathwayList(AbstractIssuerAPIEndpoint):

    def get(self, request, issuer_slug):
        """
        GET a list of learning pathways owned by an issuer
        ---
        serializer: PathwaySerializer
        """

        try:
            issuer = Issuer.cached.get(slug=issuer_slug)
        except Issuer.DoesNotExist:
            return Response("Could not find issuer", status=status.HTTP_404_NOT_FOUND)

        pathways = issuer.cached_pathways()
        serializer = PathwayListSerializer(pathways, context={
            'request': request,
            'issuer_slug': issuer_slug,
        })
        return Response(serializer.data)

    def post(self, request, issuer_slug):
        """
        Define a new pathway to be owned by an issuer
        ---
        parameters:
            - name: name
              description: The name of the new Pathway
              required: true
              type: string
              paramType: form
            - name: description
              description: A short description of the new Pathway
              required: true
              type: string
              paramType: form
            - name: alignmentUrl
              description: An optional URL that points to an external standard
              required: false
              type: string
              paramType: form
        """
        serializer = PathwaySerializer(data=request.data, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'include_structure': True
        })
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        pathway = serializer.data

        # logger.event(badgrlog.PathwayCreatedEvent(pathway))
        return Response(pathway, status=HTTP_201_CREATED)


class PathwayAPIEndpoint(AbstractIssuerAPIEndpoint):
    def _get_issuer_and_pathway(self, issuer_slug, pathway_slug):
        try:
            issuer = Issuer.cached.get(slug=issuer_slug)
        except Issuer.DoesNotExist:
            return None, None
        try:
            self.check_object_permissions(self.request, issuer)
        except PermissionDenied:
            return None, None

        try:
            pathway = Pathway.cached.get(slug=pathway_slug)
        except Pathway.DoesNotExist:
            return issuer, None
        if pathway.issuer != issuer:
            return issuer, None

        return issuer, pathway


class PathwayDetail(PathwayAPIEndpoint):

    def get(self, request, issuer_slug, pathway_slug):
        """
        GET detail on a pathway
        ---
        """
        issuer, pathway = self._get_issuer_and_pathway(issuer_slug, pathway_slug)
        if issuer is None or pathway is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if pathway.issuer != issuer:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PathwaySerializer(pathway, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'pathway_slug': pathway_slug,
            'include_structure': True,
            'include_requirements': True,
        })
        return Response(serializer.data)

    def put(self, request, issuer_slug, pathway_slug):
        """
        PUT updates to pathway details and group memberships
        ---
        serializer: PathwaySerializer
        parameters:
            - name: groups
              description: the list of groups subscribed to this pathway, as a list of ids or a list of LinkedDataReferences
              type: array
              items: {
                type: string
              }
              required: false
              paramType: form
        """
        issuer, pathway = self._get_issuer_and_pathway(issuer_slug, pathway_slug)
        if issuer is None or pathway is None or pathway.issuer != issuer:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PathwaySerializer(pathway, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

class PathwayElementList(PathwayAPIEndpoint):
    def get(self, request, issuer_slug, pathway_slug):
        """
        GET a flat list of Pathway Elements defined on a pathway
        ---
        """
        issuer, pathway = self._get_issuer_and_pathway(issuer_slug, pathway_slug)
        if issuer is None or pathway is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if pathway.issuer != issuer:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PathwaySerializer(pathway, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'pathway_slug': pathway_slug,
            'include_structure': True,
        })
        return Response(serializer.data)

    def post(self, request, issuer_slug, pathway_slug):
        """
        Add a new Pathway Element
        ---
        serializer: PathwayElementSerializer
        parameters:
            - name: parent
              description: The id or slug of the parent Pathway Element to attach to
              type: string
              required: true
              paramType: form
            - name: name
              description: The name of the Pathway Element
              type: string
              required: true
              paramType: form
            - name: description
              description: The description of the Pathway Element
              type: string
              required: true
              paramType: form
            - name: ordering
              description: The child order of this Pathway Element relative to its siblings
              type: number
              required: false
              default: 99
              paramType: form
            - name: alignmentUrl
              description: The external Alignment URL this Element aligns to
              type: string
              required: false
              paramType: form
            - name: completionBadge
              description: The id or slug of the Badge Class to award when element is completed
              type: string
              required: false
              paramType: form
            - name: requirements
              description: The CompletionRequirementSpec for the element
              type: json
              required: false
              paramType: form
            - name: children
              description: Array of ids or slugs of PathwayElements that are children of this element (ordering is preserved)
              type: array
              items: {
                type: string
              }
              required: false
              paramType: form
        """
        serializer = PathwayElementSerializer(data=request.data, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'pathway_slug': pathway_slug,
        })
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        element = serializer.data

        # logger.event(badgrlog.PathwayCreatedEvent(pathway))
        return Response(element, status=HTTP_201_CREATED)


class PathwayElementAPIEndpoint(PathwayAPIEndpoint):
    def _get_issuer_and_pathway_element(self, issuer_slug, pathway_slug, element_slug):
        issuer, pathway = self._get_issuer_and_pathway(issuer_slug, pathway_slug)
        if issuer is None or pathway is None:
            return None, None, None

        try:
            element = PathwayElement.cached.get(slug=element_slug)
        except PathwayElement.DoesNotExist:
            return issuer, pathway, None
        if element.pathway != pathway:
            return issuer, pathway, None

        return issuer, pathway, element


class PathwayElementDetail(PathwayElementAPIEndpoint):
    def get(self, request, issuer_slug, pathway_slug, element_slug):
        """
        GET detail on a pathway, starting at a particular Pathway Element
        ---
        """
        issuer, pathway, element = self._get_issuer_and_pathway_element(issuer_slug, pathway_slug, element_slug)
        if issuer is None or pathway is None or element is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PathwayElementSerializer(element, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'pathway_slug': pathway_slug,
            'include_structure': True
        })
        return Response(serializer.data)

    def put(self, request, issuer_slug, pathway_slug, element_slug):
        """
        Update a Pathway Element
        ---
        serializer: PathwayElementSerializer
        parameters:
            - name: children
              description: Array of ids or slugs of PathwayElements that are children of this element (ordering is preserved)
              type: array
              items: {
                type: string
              }
              required: false
              paramType: form
        """

        issuer, pathway, pathway_element = self._get_issuer_and_pathway_element(issuer_slug, pathway_slug, element_slug)
        if issuer is None or pathway_element is None or pathway.issuer != issuer or pathway_element.pathway != pathway:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PathwayElementSerializer(
            pathway_element,
            data=request.data,
            context={
                'request': request,
                'issuer_slug': issuer_slug,
                'pathway_slug': pathway_slug,
                'include_structure': True
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def delete(self, request, issuer_slug, pathway_slug, element_slug):
        """
        Delete a Pathway Element
        ---
        """
        issuer, pathway, element = self._get_issuer_and_pathway_element(issuer_slug, pathway_slug, element_slug)
        if issuer is None or pathway is None or element is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        element.delete()
        return Response(status=status.HTTP_200_OK)


class PathwayCompletionDetail(PathwayElementAPIEndpoint):

    def get(self, request, issuer_slug, pathway_slug, element_slug):
        """
        Get detailed completion state for a set of Recipients or Recipient Groups
        ---
        parameters:
            - name: recipientGroup[]
              description: Recipient Group(s) to return completions for
              type: array
              items: {
                type: string
              }
              required: false
              paramType: query
            - name: recipient[]
              description: Recipient(s) to return completions for
              type: array
              items: {
                type: string
              }
              required: false
              paramType: query
        """
        issuer, pathway, element = self._get_issuer_and_pathway_element(issuer_slug, pathway_slug, element_slug)
        if issuer is None or pathway is None or element is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        recipient_slugs = request.query_params.getlist('recipient[]')
        recipients = []
        for s in recipient_slugs:
            try:
                recipients.append(RecipientProfile.cached.get(slug=s))
            except RecipientProfile.DoesNotExist:
                return Response(u"Invalid Recipient '{}'".format(s), status=status.HTTP_400_BAD_REQUEST)

        group_slugs = request.query_params.getlist('recipientGroup[]')
        groups = []
        for s in group_slugs:
            try:
                groups.append(RecipientGroup.cached.get(slug=s))
            except RecipientGroup.DoesNotExist:
                return Response(u"Invalid Recipient Group '{}'".format(s), status=status.HTTP_400_BAD_REQUEST)

        for group in groups:
            recipients.extend([member.recipient_profile for member in group.cached_members()])

        recipient_completions = []
        for recipient in recipients:
            recipient_completions.append({
                'recipient': recipient,
                 'completions': recipient.cached_completions(pathway)
            })

        serializer = PathwayElementCompletionSerializer(ObjectView({
            'pathway': pathway,
            'recipientCompletions': recipient_completions,
            'recipients': recipients,
            'recipientGroups': groups
        }))

        return Response(serializer.data)
