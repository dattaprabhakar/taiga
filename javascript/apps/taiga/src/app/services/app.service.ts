/**
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * Copyright (c) 2021-present Kaleidos Ventures SL
 */

import { HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { unexpectedError } from '@taiga/core';
import { UnexpectedError } from '@taiga/data';
import { Store } from '@ngrx/store';

@Injectable({
  providedIn: 'root',
})
export class AppService {
  constructor(private store: Store) {}

  public formatHttpErrorResponse(error: HttpErrorResponse): UnexpectedError {
    return {
      message: error.message,
    };
  }

  public unexpectedError(error: HttpErrorResponse) {
    //show error 500 page
    this.store.dispatch(
      unexpectedError({
        error: this.formatHttpErrorResponse(error),
      })
    );
  }

  public toastError(
    error: HttpErrorResponse,
    data: { label: string; message: string }
  ) {
    // show toast component
    console.log('toastError', error, data);
  }
}
