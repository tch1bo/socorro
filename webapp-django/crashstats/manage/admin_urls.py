from django.conf.urls import url

from crashstats.manage import admin


app_name = 'manage'
urlpatterns = [
    url('^analyze-model-fetches/$',
        admin.analyze_model_fetches,
        name='analyze_model_fetches'),
    url('^crash-me-now/$',
        admin.crash_me_now,
        name='crash_me_now'),
    url('^debug-view/$',
        admin.debug_view,
        name='debug_view'),
    url('^graphics-devices/$',
        admin.graphics_devices,
        name='graphics_devices'),
    url('^sitestatus/$',
        admin.site_status,
        name='site_status'),
    url('^supersearch-fields/missing/$',
        admin.supersearch_fields_missing,
        name='supersearch_fields_missing'),
]
