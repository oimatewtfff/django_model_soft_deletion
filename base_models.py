from django.db import models
from django.dispatch import Signal
from django.utils import timezone

soft_deleted = Signal()
hard_deleted = Signal()


class SoftDeletionQuerySet(models.QuerySet):
    def hard_delete(self):
        for obj in self:
            obj.hard_delete()


class SoftDeletionManager(models.Manager):
    def get_queryset(self):
        return SoftDeletionQuerySet(self.model, using=self._db).filter(is_deleted=False)


class SoftDeletionModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
        soft_deleted.send(sender=self.__class__, instance=self)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def hard_delete(self, *args, **kwargs):
        hard_deleted.send(sender=self.__class__, instance=self)
        super(SoftDeletionModel, self).delete(*args, **kwargs)

    objects = SoftDeletionManager()

    all_objects = models.Manager()


def SOFT_DELETE(collector, field, sub_objs, using):
    for obj in sub_objs:
        if isinstance(obj, SoftDeletionModel):
            obj.delete()
        else:
            obj.delete()
