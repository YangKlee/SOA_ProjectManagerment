import logging

from .clients import DependencyUnavailable, academic_names_client
from .serializers import TopicResponseDTO

LOG = logging.getLogger(__name__)


def topic_response(topics, authorization, many=False):
    objects = list(topics) if many else [topics]
    majors = list(dict.fromkeys(obj.major_id for obj in objects))
    advisors = list(dict.fromkeys(obj.advisor_id for obj in objects if obj.advisor_id))
    try:
        names = academic_names_client.display_names(majors, advisors, authorization)
    except DependencyUnavailable:
        LOG.warning("Academic display-name lookup unavailable")
        names = {"major_names": {}, "advisor_names": {}}
    rows = []
    fields = set(TopicResponseDTO().fields) - {"major_name", "avisor_name"}
    for obj in objects:
        row = {field: getattr(obj, field) for field in fields}
        row["major_name"] = names["major_names"].get(obj.major_id)
        row["avisor_name"] = names["advisor_names"].get(obj.advisor_id)
        rows.append(row)
    return TopicResponseDTO(rows if many else rows[0], many=many).data
