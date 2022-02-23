/**
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * Copyright (c) 2021-present Kaleidos Ventures SL
 */

import { HttpErrorResponse } from '@angular/common/http';
import { Inject, Injectable } from '@angular/core';
import {
  TuiNotification,
  TuiNotificationOptions,
  TuiNotificationsService,
} from '@taiga-ui/core';
import {
  unexpectedError,
  forbidenError,
} from '../modules/errors/+state/actions/errors.actions';
import { ErrorManagementOptions, UnexpectedError } from '@taiga/data';
import { Store } from '@ngrx/store';
import { TranslocoService } from '@ngneat/transloco';

@Injectable({
  providedIn: 'root',
})
export class AppService {
  constructor(
    private store: Store,
    private translocoService: TranslocoService,
    @Inject(TuiNotificationsService)
    private readonly notificationsService: TuiNotificationsService
  ) {}

  public formatHttpErrorResponse(error: HttpErrorResponse): UnexpectedError {
    return {
      message: error.message,
    };
  }

  public errorManagement(
    error: HttpErrorResponse,
    errorOptions?: ErrorManagementOptions
  ) {
    const status = error.status as keyof ErrorManagementOptions;
    if (errorOptions && errorOptions[status]) {
      const config = errorOptions[status];
      if (config && config.type === 'toast') {
        return this.toastError(error, {
          label: config.options.label,
          message: config.options.message,
        });
      }
    } else if (status === 403) {
      return this.store.dispatch(
        forbidenError({
          error: this.formatHttpErrorResponse(error),
        })
      );
    } else if (status === 500) {
      return this.store.dispatch(
        unexpectedError({
          error: this.formatHttpErrorResponse(error),
        })
      );
    }
  }

  public toastError(
    error: HttpErrorResponse,
    data: { label: string; message: string }
  ) {
    const label = this.translocoService.translate(data.label);
    const message = this.translocoService.translate(data.message);
    const toastOptions: TuiNotificationOptions = {
      hasIcon: true,
      hasCloseButton: true,
      autoClose: false,
      label,
      status: TuiNotification.Error,
    };

    this.notificationsService.show(message, toastOptions).subscribe();
  }
}
